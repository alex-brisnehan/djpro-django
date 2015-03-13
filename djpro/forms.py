# coding=utf-8
from django import forms
from django.contrib import auth
from localflavor.us import forms as us

from djpro import models, ajax


class Artist(forms.ModelForm):
    class Meta:
        model = models.Artist
        fields = ('artist', 'info', 'url')
    
    class Media:
        css = {'all':('djpro/jquery.autocomplete.css',)}
        js = ('djpro/jquery.js', 'djpro/jquery-ui.js')


class Album(forms.ModelForm):
    artist = ajax.ArtistField(required=False)
    
    class Media:
        css = {'all':('djpro/jquery.autocomplete.css',)}
        js = ('djpro/jquery.js', 'djpro/jquery-ui.js', 'jquery.combobox.js', 'djpro/ages.js')
    
    class Meta:
        model = models.Album
        fields = ('album', 'artist', 'label', 'year', 'review', 'location')


class Song(forms.ModelForm):
    rating = forms.TypedChoiceField(required=False, choices=(('', u''), (2, u'★'), (3, u'★★'), (4, u'★★★'), (5, u'★★★★'), (0, u'dirty')), label=u'Rating', coerce=int, empty_value=1)
    comp_artist = ajax.ArtistField(required=False, label=u'Artist')
    
    def clean(self):
        data = self.cleaned_data
        if self._errors.get('comp_artist') is None and data['comp_artist'] is None and data['album'].artist is None:
            self._errors['comp_artist'] = forms.util.ErrorList([u'All songs on a compilation require an artist'])
            del data['comp_artist']
        return data
    
    class Meta:
        model = models.Song
        fields = ('track', 'song', 'comp_artist', 'length', 'ramp', 'post', 'tempo', 'rating', 'album')

# I’m not using the formset factories because I object to factory functions. The 
# difference between what I did and just dumping all the info in a foctory function
# is trivial, but sometimes you’ve got to take a stand.
class SongSet(forms.models.BaseInlineFormSet):
    form = Song
    model = models.Song
    fk = model._meta.get_field('album')
    extra = 2
    can_delete = True
    can_order = False
    max_num = None
    absolute_max = 100
    
    def add_fields(self, form, i):
        super(SongSet, self).add_fields(form, i)
        if not form.instance.can_delete() and self.can_delete:
            form.fields['DELETE'].widget = forms.HiddenInput()
            form.fields['DELETE'].clean = lambda a: False
    
    # Minimum of 5 forms
    def total_form_count(self):
        tfc = super(SongSet, self).total_form_count()
        if tfc < 5:
            return 5
        return tfc

class MiniSong(forms.ModelForm):
    # Used in album view for a quick add.
    comp_artist = ajax.ArtistField(required=False, label=u'Artist')
    album = forms.ModelChoiceField(models.Album.objects.all(), widget=forms.HiddenInput())
    
    def clean(self):
        data = self.cleaned_data
        if self._errors.get('comp_artist') is None and data['comp_artist'] is None and data.get('album') and data['album'].artist is None:
            self._errors['comp_artist'] = forms.util.ErrorList(['All songs on a compilation require an artist'])
            del data['comp_artist']
        return data
    
    class Media:
        js = ('djpro/jquery.js', 'djpro/add_new_song.js',)
    
    class Meta:
        model = models.Song
        fields = ('album', 'song', 'comp_artist',)

class Concert(forms.ModelForm):
    fields = ('date', 'time', 'venue', 'minimum_age', 'site', 'we_present', 'info')
    
    minimum_age = forms.CharField(required=False, widget=forms.TextInput(attrs={'class':'ages', 'size':'4'}))
    
    class Media:
        js = ('djpro/jquery.js', 'djpro/jquery-ui.js', 'jquery.combobox.js', 'djpro/ages.js',)
    
    class Meta:
        model = models.Concert

class Performer(forms.ModelForm):
    # opt_artist is the autocomplete code for a normal text field
    # that encourages you to use an existing artist
    performer = forms.CharField(required=False, widget=forms.TextInput(attrs={'class':'opt_artist'}))
    
    class Media:
        css = {'all':('djpro/jquery.autocomplete.css',)}
        js = ('djpro/jquery.js', 'djpro/jquery-ui.js', 'djpro/artist_ajax.js',)
    
    class Meta:
        model = models.Performer
        fields = ('performer', 'concert',)


class PerformerSet(forms.models.BaseInlineFormSet):
    form = Performer
    model = models.Performer
    fk = model._meta.get_field('concert')
    extra = 3
    can_delete = False
    can_order = False
    max_num = None
    absolute_max = 100
    
    def clean(self):
        for f in self.forms:
            if f['performer'].data: 
                return
        raise forms.ValidationError, u'There has to be at least one artist performing'

    # Minimum of 5 forms
    def total_form_count(self):
        tfc = super(PerformerSet, self).total_form_count()
        if tfc < 5:
            return 5
        return tfc


class UserProfile(forms.ModelForm):
    phone = us.USPhoneNumberField(required=False)
    
    class Meta:
        model = models.UserProfile
        exclude = ('user',)

class User(forms.ModelForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = auth.models.User
        fields = ('first_name', 'last_name', 'email',)
