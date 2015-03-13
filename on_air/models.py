# encoding: utf-8

from django.db import models
from djpro import models as dj

from django.core.exceptions import PermissionDenied

# The most important model of this entire thing. All hail the playlist.
class Playlist(models.Model):
    order = models.FloatField(unique=True)
    song = models.ForeignKey(dj.Song, null=True, blank=True)
    played_at = models.DateTimeField(null=True, blank=True, db_index=True)
    
    # One thing to keep in mind: if a.played_at < b.played_at then 
    # a.order < b.order. Order is used to sort the playist for display, 
    # but only played_at is retained. Thus, it's possible that the sort
    # in the future will be different than it is now. Not a good idea.
    
    class Meta:
        ordering = ['order']
        verbose_name = u"Playlist line"


# Everything I've found on the internet says that rotation should be 
# scheduled by hourly "clocks". You are more than welcome to implement 
# that instead of this for the entire day.
class RotationSchedule(models.Model):
    #ideally order is 1-n with no gaps. Not likely without some more work.
    order = models.IntegerField(unique=True) 
    rotation = models.ForeignKey(dj.Rotation, null=True, blank=True)
    
    def save(self, *args, **kwargs):
        if (self.order == None):
            self.order = (RotationSchedule.objects.aggregate(models.Max('order'))['order__max'] or 0) + 1
        return super(RotationSchedule, self).save(*args, **kwargs)
    
    class Meta:
        ordering = ['order']
        verbose_name = u'Schedule Entry'
        verbose_name_plural = u'Rotation Schedule'


# History of played songs. The most number of rows by a factor of 100
class PlayHistory(models.Model):
    song = models.ForeignKey(dj.Song, on_delete=models.PROTECT)
    played_at = models.DateTimeField(unique=True)
    
    class Meta:
        ordering = ['played_at']
    
    def delete():
        """
        No deleting!
        """
        raise PermissionDenied


# I don't like the name of this class since I want to encourge bigger 
# numbers, but don't know what to call it.
class Top10(models.Model):
    week_ending = models.DateField(unique=True)
    
    class Meta:
        verbose_name = u'Top 10 list'
        ordering = ('-week_ending', )
    
    def __unicode__(self):
        return u'Top %d ending %s' % (self.albums.count(), self.week_ending)

class Top10Album(models.Model):
    week = models.ForeignKey(Top10, related_name="albums")
    rank = models.IntegerField(db_index=True, blank=True)
    album = models.ForeignKey(dj.Album)
    count = models.IntegerField(null=True, blank=True)
    
    class Meta:
        unique_together = ('week', 'album'),
        ordering = ['rank']
        verbose_name = "Top 10 List Line"
        
    def __unicode__(self):
        if self.count:
            return u'#%d: “%s” was played %d times in the past week' % (self.rank, self.album, self.count)
        return u'#%d: %s' % (self.rank, self.album)

class TuneTrackerLog(models.Model):
    """
    When Tune Tracker adds a song to the playlist, it gets recorded here until requested by the onair playlist.
    """
    playlist = models.ForeignKey(Playlist, null=True, blank=True)  
    
    

