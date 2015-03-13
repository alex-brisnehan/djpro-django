# coding: utf-8
import datetime
import re

from django.db.models import *
from django.core.urlresolvers import reverse
from django.core.exceptions import PermissionDenied, ValidationError

from djpro import extras

# Create your models here.

class Artist(Model):
    """
    A model representing a band or musician.
    
    Most of the models have extra “search” and “sort” fields that are derived
    from the actual name.
    
    >>> a = Artist(artist=u"The \xdfand")
    >>> a.save()
    >>> a.artist
    u'The \\xdfand'
    >>> a.search
    u'the band'
    >>> a.sort
    u'band, the'
    """
    artist = CharField('Artist name', max_length=255, unique=True)
    search = CharField(max_length=255, unique=True)
    sort = CharField(max_length=255, db_index=True)
    last_played = DateTimeField('last played at', null=True, blank=True)
    times_played = IntegerField('number of times played', default=0)
    info = TextField(blank=True)
    url = URLField(blank=True)
    
    class Meta:
        ordering = ["sort"]
    
    def next_concert(self):
        if hasattr(self, "_next_concert_cache"):
            return self._next_concert_cache
        concerts = self.concert_set.all().select_related('venue').order_by('date')
        if concerts.count() > 0:
            self._next_concert_cache = concerts[0]
        else:
            self._next_concert_cache = None
        return self._next_concert_cache
    
    def __unicode__(self):
        return self.artist
    
    def save(self, *args, **kwargs):
        self.artist = self.artist.strip()
        self.search = extras.ugam(self.artist).lower()
        self.sort = extras.sans_the(self.search)
        return super(Artist, self).save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('djpro.views.artist_view', kwargs = {'id': self.id})
    
    def played_recently(self):
        """
        Has the artist been played in the past n days?
        """
        if not self.last_played:
            return False
        return datetime.datetime.now() - self.last_played < datetime.timedelta(2, 14400) # 2 days 4 hours
    
    def validate_unique(self, exclude=None):
        # Since search is both unique and calculated from artist, we need 
        # artist to be unique for search. That is, if search isn't unique,
        # we blame artist.
        super(Artist, self).validate_unique(exclude)
        
        if "artist" in exclude:
            return
        
        qs = Artist.objects.filter(search=extras.ugam(self.artist).lower())
        if self.pk is not None:
            qs = qs.exclude(pk=self.pk)
        if qs.exists():
            raise ValidationError({'artist':(u'An artist named ‘%s’ already exists' % qs[0].artist, )})


class Album(Model):
    """
    The model for albums.
    
    The location convention is “NIL” stands for “Not In Libary”.
    
    >>> al = Album(album=u"An Album", year=2000, label=u"label", location=u"NIL")
    >>> al.save()
    >>> al.sort
    u'album, an'
    >>> al.is_compilation()
    True
    """
    album = CharField('Album name', max_length=255)
    # More denormalized fields
    search = CharField(max_length=255, db_index=True)
    sort = CharField(max_length=255, db_index=True)
    artist = ForeignKey(Artist, null=True, blank=True)
    label = CharField(max_length=200, null=True, db_index=True)
    review = TextField(blank=True)
    year = IntegerField('year first released', null=True, db_index=True)
    location = CharField(max_length=25, db_index=True)
    added_on = DateField('date added to the library', auto_now_add=True, null=True, blank=True)
    
    
    def __unicode__(self):
        return self.album
        
    class Meta:
        ordering = ['sort']
    
    def save(self, *args, **kwargs):
        self.album = self.album.strip()
        self.search = extras.ugam(self.album).lower()
        self.sort = extras.sans_the(self.search)
        if self.location.lower() == u'nil':
            self.location == u'NIL'
        return super(Album, self).save(*args, **kwargs)
    
    def get_absolute_url(self):
        return reverse('djpro.views.album_view', kwargs = {'id': self.id})
    
    def is_compilation(self):
        if hasattr(self, '_is_compilation_value'):
            return self._is_compilation_value
        self._is_compilation_value = self.artist is None or self.song_set.filter(comp_artist__isnull=False).count() > 0
        return self._is_compilation_value


class Song(Model):
    """
    Model of the song.
    """
    song = CharField('Song name', max_length=255)
    # One denormalized field
    search = CharField(max_length=255, null=True, db_index=True)
    album = ForeignKey(Album)
    comp_artist = ForeignKey(Artist, related_name='comp_songs', null=True, blank=True)
    # Two denormalized fields. Makes look ups faster.
    artist = ForeignKey(Artist, related_name='all_songs', null=True)
    length = CharField(max_length=6, null=True, blank=True) #I don’t like this. An interval field would be more accurate.
    last_played = DateTimeField('last played at', null=True, blank=True)
    times_played = IntegerField('number of times played', default=0)
    track = CharField(max_length=5, null=True, blank=True)
    # The track as an int, for sorting. So three denormalaized fields.
    track_num = IntegerField(null=True, blank=True, db_index=True)
    tempo = CharField(max_length=5, null=True, blank=True)
    ramp = CharField(max_length=5, null=True, blank=True)
    post = CharField(max_length=5, null=True, blank=True)
    # Known values for rating: 1-5, 0:dirty, -2:DJ Pick
    RATING_CHOICES = (
        (1, u''), 
        (2, u'★'), 
        (3, u'★★'), 
        (4, u'★★★'), 
        (5, u'★★★★'), 
        (0, u'dirty'), 
        (-2, u'DJ pick'),
        (-3, u'TuneTracker'),
    )
    rating = SmallIntegerField(default=1, choices=RATING_CHOICES)
    rotation = ForeignKey('Rotation', null=True, blank=True)
    added_on = DateField(auto_now_add=True, blank=True, null=True)

    def __unicode__(self):
        return self.song
    
    
    class Meta:
        ordering = ['track_num', 'song']
    
    def save(self, *args, **kwargs):
        self.song = self.song.strip()
        self.search = extras.ugam(self.song).lower()
        self.artist = self.comp_artist or self.album.artist
        
        # Common track listing styles: '', '12', '1-3', 'B 7'
        # Otherwise, we’ll have to guess
        if not self.track:
            self.track_num = None
        elif re.match(r'^[0-9]+$', self.track):
            self.track_num = int(self.track)
        elif re.match(r'^([0-9]+)[^0-9]+([0-9]+)$', self.track):
            mat = re.match(r'^([0-9]+)[^0-9]+([0-9]+)$', self.track)
            self.track_num = 100*int(mat.groups()[0]) + int(mat.groups()[1])
        elif re.match(r'^([A-Z])[^0-9]*([0-9]+)$', self.track, re.I):
            mat = re.match(r'^([A-Z])[^0-9]*([0-9]+)$', self.track, re.I)
            self.track_num = 100*ord(mat.groups()[0]) + int(mat.groups()[1])
        elif re.match(r'[0-9]+', self.track):
            self.track_num = int(re.match(r'[0-9]+', self.track).group())
        else:
            self.track_num = None
        
        return super(Song, self).save(*args, **kwargs)
    
    def can_delete(self):
        """
        Some songs must not be deleted. Here’s how we know.
        """
        return not (hasattr(self, 'playhistory_set') and self.playhistory_set.count() > 0)
    
    def delete(self):
        if not self.can_delete():
            raise PermissionDenied("You can not delete the song %s" % self.song)
        return super(Song, self).delete()
    
    def played_recently(self):
        """
        Has the song or artist been played in the past n days?
        """
        if self.artist and self.artist.played_recently():
            return True
        if not self.last_played:
            return False
        return (datetime.datetime.now() - self.last_played < datetime.timedelta(8, 14400)) # 8 days 4 hours
    
    

# Concert classes

class Concert(Model):
    venue = ForeignKey('Venue')
    date = DateField(db_index=True)
    time = TimeField(blank=True, null=True, db_index=True)
    we_present = BooleanField('Radio 1190 presents', default=False)
    minimum_age = CharField(max_length=4, blank=True)
    info = TextField(blank=True)
    site = URLField(blank=True)
    artists = ManyToManyField('Artist', through='Performer', blank=True)
    
    class Meta:
        ordering = ['date', 'time']
    
    def __unicode__(self):
        return u"%s @ %s" % (self.date, self.venue)
    

class Performer(Model):
    """
    Model for performers at a concert.
    
    There are many things a “Performer” could be, including a band, movie,
    or concert title. We want a back link if it’s actually a band, but we 
    don’t want to enforce it. So we look up the artist name, and if there’s
    a match, then we create a link.
    """
    concert = ForeignKey(Concert)
    order = SmallIntegerField()
    performer = CharField(max_length=255)
    artist = ForeignKey(Artist, null=True, blank=True)
    
    def get_absolute_url(self):
        if self.artist:
            return self.artist.get_absolute_url()
        return None
    
    def save(self):
        try:
            self.artist = Artist.objects.get(search=extras.ugam(self.performer).lower())
        except:
            self.artist = None
        return super(Performer, self).save()
    
    def __unicode__(self):
        return self.performer

    class Meta:
        ordering = ['order']


class Venue(Model):
    venue = CharField(max_length=255, unique=True)
    # only one denormalized field this time
    sort = CharField(max_length=255, null=True, db_index=True)
    location = CharField(max_length=255, blank=True)
    default_minimum_age = CharField(max_length=4, blank=True) #for bars
    default_time = TimeField(blank=True, null=True)
    homepage = URLField(blank=True)

    def __unicode__(self):
        return self.venue

    class Meta:
        ordering = ['venue']
       
    def save(self, *args, **kwargs):
        self.sort = extras.sans_the(self.venue)
        super(Venue, self).save()


# other supporting fields

class Rotation(Model):
    rotation = CharField(max_length=35)
    max = SmallIntegerField('Suggested number') # Nonsense, but sometimes useful nonsense

    def __unicode__(self):
        return self.rotation

    class Meta:
        verbose_name = "rotation level"
        verbose_name_plural = "rotation"
        ordering = ['max']

# User profile model. Please subclass and extend to your hearts delight!

from django.contrib.auth.models import User

class UserProfile(Model):
    user = OneToOneField(User)
    alias = CharField(max_length=75, null=True)
    phone = CharField(max_length=15, null=True, blank=True)

    def save(self, *args, **kwargs):
        if self.alias == '' or self.alias is None and self.user.last_name:
            self.alias = u'%s %s.' % (self.user.first_name, self.user.last_name[0])
        super(UserProfile, self).save(*args, **kwargs)

"""
>>> art = Artist(artist=u'Artist')
>>> art.save()
>>> al = Album(album=u'album', year=2010, label=u"lab", location=u"123")
>>> al.artist = art
>>> al.save()
>>> s1 = Song(song=u'First Song', album=al, track=u'1-1')
>>> s1.save()
>>> s2 = Song(song=u'Second Song', album=al, track=u'2-1')
>>> s2.save()
>>> s3 = Song(song=u'Third Song', album=al, track=u'1-10')
>>> s3.save()

>>> list(al.song_set.all()) == [s1, s3, s2]
True
>>> s1.artist
<Artist: Artist>
"""
