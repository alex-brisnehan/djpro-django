# This file is for all the AJAX stuff. Form fields, views, etc.

from djpro import models, extras

from django import forms
from django.http import HttpResponse
from django.utils.html import escape, mark_safe

import json

class ArtistWidget(forms.TextInput):
    """
    A Widget that provides a textinput instead of popup menu, but 
    only for artists. Only used with ajax.ArtistField.
    """
    def render(self, name, value, attrs={}):
        attrs.update({'class':'artist'})
        if isinstance(value, int):
            value = models.Artist.objects.get(pk=value).artist
        return super(ArtistWidget, self).render(name, value, attrs)
    
    class Media:
        css = {'all':('djpro/jquery.autocomplete.css',)} 
        css = {'all':('djpro/jquery.autocomplete.css',)} 
        js = ('djpro/jquery.js', 'djpro/jquery-ui.js', 'djpro/artist_ajax.js',)

class ArtistField(forms.Field):
    """
    A form Field that returns an artist and uses ArtistWidget.
    """
    widget = ArtistWidget
    
    def to_python(self, value):
        if not value or value=='':
            return None 
        try:
            return models.Artist.objects.get(artist__exact=value)
        except models.Artist.DoesNotExist:
            raise forms.ValidationError(u"There is no artist named %s." % value)

class AlbumWidget(forms.Widget):
    def render(self, name, value, attrs=None):
        try:
            value = value or 0
            a = models.Album.objects.all().select_related('artist').get(pk=value)
            artist = a.artist and a.artist.artist or u''
            album = a.album or u''
            pk = value or u''
        except models.Album.DoesNotExist:
            artist = album = pk = u''
        
        artist_attrs = self.build_attrs(attrs, type="text", value=artist, name=u"%s_artist"%name)
        artist_attrs.update({'id' : (u'id_%s_artist'%name), 'placeholder': 'Compilation'})
        album_attrs = self.build_attrs(attrs, type="text", value=album, name=u"%s_album"%name)
        album_attrs.update({"id" : (u"id_%s_album"%name)})
        pk_attrs = self.build_attrs(attrs, type="hidden", value=pk, name=u"%s_pk"%name)
        pk_attrs.update({"id" : (u"id_%s_pk"%name)})
        return mark_safe(u"<input %s /><input %s /><input %s /><script>artist_combo(\"%s\")</script>" % (forms.util.flatatt(artist_attrs), forms.util.flatatt(album_attrs), forms.util.flatatt(pk_attrs), escape(name)))
    
    def value_from_datadict(self, data, files, name):
        return data.get(u"%s_pk" % name, None)
    
    class Media:
        css = {'all':('djpro/jquery.autocomplete.css',)}
        js = ('djpro/jquery.js', 'djpro/jquery-ui.js', 'djpro/album_ajax.js',)
    
class AlbumField(forms.Field):
    widget = AlbumWidget
    
    def to_python(self, value):
        if not value or value=='':
            return None 
        try:
            return models.Album.objects.get(pk=value)
        except models.Album.DoesNotExist:
            raise forms.ValidationError(u"This does not match an album.")


def artist_list(request):
    """
    View used by the autocomplete
    """
    term = request.GET.get('term', '').strip()
    if term == '':
        return HttpResponse('')
    term = extras.ugam(term).lower();
    artist_list = models.Artist.objects.filter(search__contains=term).extra(select={'len':'length(artist)'}, order_by=['len'])[:5]
    results = [d.artist for d in artist_list]
    return HttpResponse(json.dumps(results), content_type="text/json")

def album_list(request):
    """
    View used by AlbumWidget
    """
    if not request.GET.get('album'):
        return  HttpResponse('')
    
    album = request.GET['album'].strip()
    artist = request.GET.get('artist', u'').strip()
    if artist == u'':
        qs = models.Album.objects.filter(artist__isnull=True)
    else:
        qs = models.Album.objects.filter(artist__artist=artist)
        
    qs = qs.filter(search__contains=extras.ugam(album).lower()).extra(select={'len':'length(album)'}, order_by=['len'])[:5]
    
    results = [{'value':a.album, 'location':a.location, 'id':a.pk} for a in qs]
    return HttpResponse(json.dumps(results), content_type="text/json")

