# coding: utf-8

from django.http import HttpResponse, HttpResponseRedirect
from django.template.loader import get_template
from django.template import Context, RequestContext
#from django.utils import simplejson
from django.core.urlresolvers import reverse
from django.db import transaction as trans
from django.contrib import auth
from django.contrib.auth import decorators as auth_dec
from django.contrib import messages
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import render_to_response, get_object_or_404
from django.conf import settings

from djpro import models, forms, extras

# I can use LOGIN_URL with impunity, but not the site specific version.
LOGIN_URL = getattr(settings, "DJPRO_LOGIN_URL", settings.LOGIN_URL)

def front(request):
    # I want this to be both login and main page.
    if not request.user.is_authenticated():
        return auth.views.login(request, template_name='djpro/login.html')
        
    return render_to_response('djpro/front.html', {}, context_instance=RequestContext(request));


def search(request):
    if not request.GET.get('value'):
        # If there is no search term, give them another chance
        return render_to_response('djpro/search_empty.html', {}, context_instance=RequestContext(request))

    s_for = request.GET.get('for')
    s_value = request.GET['value'].strip()
    
    if s_for == 'Artist':
        results = models.Artist.objects.filter(search__contains=extras.ugam(s_value).lower())
        if results.count() > 0:
            return render_to_response('djpro/search_artist.html', {'artist_list':results, 'for':s_for, 'value':s_value}, context_instance=RequestContext(request))

    if s_for == 'Album':
        results = models.Album.objects.filter(search__contains=extras.ugam(s_value).lower())
        if results.count() > 0:
            return render_to_response('djpro/search_album.html', {'album_list':results, 'for':s_for, 'value':s_value}, context_instance=RequestContext(request))
        
    if s_for == 'Location':
        results = models.Album.objects.filter(location__icontains=s_value).order_by('location')
        if results.count() > 0:
            return render_to_response('djpro/search_album.html', {'album_list':results, 'for':s_for, 'value':s_value}, context_instance=RequestContext(request))
        
    if s_for == 'Song':
        results = models.Song.objects.filter(search__contains=extras.ugam(s_value).lower(), rating__gt=-2).order_by('song')
        # we need the order_by because the default is to sort by track number first
        if results.count() > 0:
            return render_to_response('djpro/search_song.html', {'song_list':results, 'for':s_for, 'value':s_value}, context_instance=RequestContext(request))
        
    if s_for == 'Label':
        results = models.Album.objects.filter(label__icontains=s_value).order_by('label', 'sort')
        if results.count() > 0:
            return render_to_response('djpro/search_album.html', {'album_list':results, 'for':s_for, 'value':s_value}, context_instance=RequestContext(request))
        
    # If there is no search term or no results, 404
    return render_to_response('djpro/search_empty.html', {'for':s_for, 'value':s_value}, context_instance=RequestContext(request))


# -----------------------------------------------
# Artist crud


def artist_view(request, id):
    artist = get_object_or_404(models.Artist, pk=id)
    concerts = artist.concert_set.all().select_related('venue')
    if request.GET.get('show') == 'songs':
        request.session['artist_view'] = 'all_songs'
    elif request.GET.get('show') == 'albums':
        request.session['artist_view'] = 'albums'
    
    if request.session.get('artist_view') == 'all_songs':
        songs = artist.all_songs.filter(rating__gt=-2).select_related('album')
        return render_to_response('djpro/artist_with_songs.html', {'artist': artist, "songs":songs, "concerts":concerts}, context_instance=RequestContext(request))
    albums = artist.album_set.all()
    songs = artist.comp_songs.filter(rating__gt=-2).select_related('album')
    return render_to_response('djpro/artist_with_albums.html', {'artist':artist, "albums":albums, "songs":songs, "concerts":concerts}, context_instance=RequestContext(request))


@auth_dec.permission_required('djpro.change_artist', login_url=LOGIN_URL)
def artist_edit(request, id):
    artist = get_object_or_404(models.Artist, pk=id)

    if request.method == 'POST':
        form = forms.Artist(request.POST, instance=artist)
        if form.is_valid():
            artist = form.save()
            messages.info(request, u"Saved changes to artist “%s”" % (artist.artist))
            return HttpResponseRedirect(artist.get_absolute_url())
    else:
        form = forms.Artist(instance=artist)
    return render_to_response('djpro/artist_edit.html', {'artist':artist, 'form':form}, context_instance=RequestContext(request))


@auth_dec.permission_required('djpro.add_artist', login_url=LOGIN_URL)
def artist_new(request):
    if request.method == 'POST':
        form = forms.Artist(request.POST)
        if form.is_valid():
            artist = form.save()
            messages.info(request, u"Saved new artist “%s”" % artist.artist)
            return HttpResponseRedirect(artist.get_absolute_url())

    else:
        form = forms.Artist()

    return render_to_response('djpro/artist_edit.html', {'form':form}, context_instance=RequestContext(request))

# -----------------------------------------------
# Album crud

def album_view(request, id):
    album = get_object_or_404(models.Album, pk=id)
    songs = album.song_set.filter(rating__gt=-2).select_related('comp_artist')
    song_form = forms.MiniSong(initial={'album':album.id})
    return render_to_response('djpro/album.html', {'album':album, "songs":songs, 'song_form':song_form}, context_instance=RequestContext(request))


@auth_dec.permission_required('djpro.change_album', login_url=LOGIN_URL)
def album_edit(request, id):
    album = get_object_or_404(models.Album, pk=id)
    songs = models.Song.objects.filter(rating__gt=-2).select_related('comp_artist')
    
    if request.method == 'POST':
        form = forms.Album(request.POST, instance=album)
        song_forms = forms.SongSet(request.POST, instance=album, queryset=songs)
        if form.is_valid() and song_forms.is_valid():
            form.save()
            song_forms.save()
            messages.info(request, u"Saved changes to album “%s”" % album)
            return HttpResponseRedirect(album.get_absolute_url())
    
    else:
        form = forms.Album(instance=album)
        song_forms = forms.SongSet(instance=album, queryset=songs)
        
    return render_to_response('djpro/album_edit.html', {'form':form, 'song_forms':song_forms}, context_instance=RequestContext(request))


@auth_dec.permission_required('djpro.add_album', login_url=LOGIN_URL)
def album_new(request):
    if request.method == 'POST':
        album_form = forms.Album(request.POST)
        
        if album_form.is_valid():
            album = album_form.save(commit=False)
            song_forms = forms.SongSet(request.POST, instance=album)
        
            if song_forms.is_valid():
                album.save()
                song_forms.save()
                messages.info(request, u"Saved new album “%s”" % album)
                return HttpResponseRedirect(album.get_absolute_url())
        else: #We need the song_forms validated
            song_forms = forms.SongSet(request.POST)
            
    else:
        album_form = forms.Album(initial={'artist': request.GET.get('artist')})
        song_forms = forms.SongSet()
        
    return render_to_response('djpro/album_edit.html', {'form':album_form, 'song_forms':song_forms}, context_instance=RequestContext(request))

@auth_dec.permission_required('djpro.add_song', login_url=LOGIN_URL)
def add_song(request):
    #Used for adding a single song to an exgisting album in an AJAX way
    song_f = forms.MiniSong(request.POST)
    if song_f.is_valid():
        return render_to_response('djpro/song.html', {'song':song_f.save()}, context_instance=RequestContext(request))
    else:
        return HttpResponse(song_f.errors.as_text(), content_type='text/plain')

#-----------------------------------------
# Concert stuff

def concert_list(request):
    concerts = models.Concert.objects.all();
    return render_to_response('djpro/concert_list.html', {'concerts':concerts}, context_instance=RequestContext(request))

@auth_dec.permission_required('djpro.add_concert', login_url=LOGIN_URL)
def concert_new(request):
    if request.method == 'POST':
        concert = models.Concert()
        concert_f = forms.Concert(request.POST, instance=concert)
        performers_f = forms.PerformerSet(request.POST, instance=concert)
        
        if concert_f.is_valid() and performers_f.is_valid():
            concert_f.save(commit=False).save()
            i = 0
            for f in performers_f.forms:
                if f['performer'].data:
                    performer = f.save(commit=False)
                    performer.order = i
                    performer.concert = concert
                    performer.save()
                    i+=1
            messages.info(request, u"Saved new concert “%s”" % concert)
            return HttpResponseRedirect(reverse('djpro.views.concert_list'), )
            
    else:
        concert_f = forms.Concert()
        performers_f = forms.PerformerSet()
        
    return render_to_response('djpro/concert_edit.html', {'concert': concert_f, 'performers': performers_f, 'media':(concert_f.media + performers_f.forms[0].media)}, context_instance=RequestContext(request))

@auth_dec.permission_required('djpro.delete_concert', login_url=LOGIN_URL)
def concert_delete(request):
    if request.method == "POST" and request.POST['id']:
        concert = models.Concert.objects.get(pk=request.POST['id'])
        concert.delete()
        messages.info(request, u"Deleted concert “%s”" % concert)
    return HttpResponseRedirect(reverse('djpro.views.concert_list'))

@auth_dec.permission_required('djpro.change_concert', login_url=LOGIN_URL)
def concert_edit(request, id):
    concert = get_object_or_404(models.Concert, pk=id)
    
    if request.method == "POST":
        concert_f = forms.Concert(request.POST, instance=concert)
        performers_f = forms.PerformerSet(request.POST, instance=concert)
        
        if concert_f.is_valid() and performers_f.is_valid():
            concert_f.save(commit=False).save()
            i=0
            for f in performers_f.forms:
                performer = f.save(commit=False)
                if performer.performer:
                    performer.order = i
                    performer.concert = concert
                    performer.save()
                    i+=1
                else:
                    if performer.id:
                        performer.delete()
                
            messages.info(request, u"Saved changes to concert “%s”" % concert)
            return HttpResponseRedirect(reverse('djpro.views.concert_list'))
            
    
    else:
        concert_f = forms.Concert(instance=concert)
        performers_f = forms.PerformerSet(instance=concert)
    
    return render_to_response('djpro/concert_edit.html', {'concert': concert_f, 'performers': performers_f, 'media':(concert_f.media + performers_f.forms[0].media)}, context_instance=RequestContext(request))

def edit_profile(request):
    # Get the profile
    user = request.user
    try:
        profile = user.userprofile
    except ObjectDoesNotExist:
        profile = models.UserProfile(user=user).save()

    if request.method=="POST":
        if request.POST.get('old_password'):
            pass_f = auth.forms.PasswordChangeForm(user, request.POST)
            if pass_f.is_valid():
                pass_f.save()
                messages.info(request, u"Changed your password")
                return HttpResponseRedirect(reverse('djpro.views.front'))

            user_f = forms.User(instance=user)
            profile_f = forms.UserProfile(instance=profile)
        
        else:
            user_f = forms.User(request.POST, instance=user)
            profile_f = forms.UserProfile(request.POST, instance=profile)
            if profile_f.is_valid() and user_f.is_valid():
                user_f.save()
                profile_f.save()
                messages.info(request, u"Changed your profile")
                return HttpResponseRedirect(reverse('djpro.views.front'))
            
            pass_f = auth.forms.PasswordChangeForm(user)
            
    else:
        user_f = forms.User(instance=user)
        profile_f = forms.UserProfile(instance=profile)
        pass_f = auth.forms.PasswordChangeForm(user)
        
    return render_to_response('djpro/profile.html', {'user_form': user_f, 'profile': profile_f, 'password': pass_f}, context_instance=RequestContext(request))


