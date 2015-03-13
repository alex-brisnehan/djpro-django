# coding: utf-8

import datetime, json

from django.db import transaction
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from django.core.urlresolvers import reverse
from django.template import Template, Context, RequestContext
from django.template.loader import get_template
from django.utils.safestring import mark_safe
from django.contrib import auth
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt

from on_air import models
from djpro import forms
from djpro import extras

# I can use LOGIN_URL with impunity, but not the site specific version.
LOGIN_URL = getattr(settings, "ONAIR_LOGIN_URL", settings.LOGIN_URL)

def onair(request):
    if not request.user.has_perm('on_air.change_playlist'):
        return auth.views.login(request, template_name='on_air/login.html')
    
    # This is the big one. All 200 songs for today are displayed with controls
    # for changing them. It can get slow. Please, please re-work this

    # Separate into things played more than twenty minutes ago, and everything else
    last_played = datetime.datetime.now() - datetime.timedelta(0, 20*60)
    last_played = models.Playlist.objects.filter(played_at__lt = last_played).order_by('-order')
    
    if last_played.exists():
        last_played = last_played[0].order
        older_list = models.Playlist.objects.filter(order__lte = last_played).select_related('song__artist', 'song__album').prefetch_related('song__artist__concert_set__venue')
        playlist = models.Playlist.objects.filter(order__gt = last_played).select_related('song__artist', 'song__album').prefetch_related('song__artist__concert_set__venue')
    else:
        older_list = []
        playlist = models.Playlist.objects.all().select_related('song__artist', 'song__album').prefetch_related('song__artist__concert_set__venue')
    
    models.TuneTrackerLog.objects.all().delete()
    dj_pick = {}
    for line in playlist:
        if line.song and (line.song.rating == -2):
            # Wrong wrong wrong! Fix this!
            if not dj_pick.get(line.song.id):
                songs = list(models.dj.Song.objects.filter(rating__gt=0, album=line.song.album_id, last_played__isnull=True).order_by("?")) + list(models.dj.Song.objects.filter(rating__gt=0, album=line.song.album_id, last_played__isnull=False).order_by("last_played"))
                # pick menu has one %d 
                dj_pick[line.song.id] = get_template('on_air/pick_menu.html').render(Context({'songs':songs}))
            line.menu = mark_safe(dj_pick[line.song.id].replace(u'⚛line id⚛', unicode(line.id)))
        
    return render_to_response('on_air/playlist.html', {'playlist':playlist, 'old_played':older_list, 'user':request.user})


# These all are called by AJAX

# There are two kinds of AJAX calls: Those that return HTML, and those that change 
# playlist times. If the play time is changed, they are likely many lines with
# changes. Thus a JSON of id:time is returned. 

@auth.decorators.permission_required('on_air.change_playlist', login_url=LOGIN_URL)
def move(request):
    # This view is quite complex because we probably also need to change one or
    # more played_at. See the note in the Playlist model.
    
    if request.method == "POST" and request.POST['id'] and request.POST['after']:
        id = request.POST['id']
        after = request.POST['after']
        line = get_object_or_404(models.Playlist, pk=id)
        old_order = line.order
        
        if after == 'top':
            new_order = models.Playlist.objects.all().order_by('order')[0].order - 1.0
        else:
            new_order = models.Playlist.objects.get(pk=after).order
            new_order = (new_order + models.Playlist.objects.filter(order__gt=new_order).order_by('order')[0].order) / 2
        line.order = new_order
        line.save()
        
        # Possible situations: 
        #
        # The line is being moved one: swap the times
        if old_order < new_order:
            moved_lines = models.Playlist.objects.filter(order__gt=old_order, order__lt=new_order)
        else:
            moved_lines = models.Playlist.objects.filter(order__gt=new_order, order__lt=old_order)
        
        if moved_lines.count() == 1:
            other_line = moved_lines[0]
            temp = line.played_at
            line.played_at = other_line.played_at
            other_line.played_at = temp
            line.save()
            other_line.save()
            return render_to_response('on_air/changed_times.json', {'list':[line, other_line]}, content_type="application/json")
        
        # All other possibilities are awkward. In order to maintain the rule that
        # played_at < played_at means order < order, it's simplist to just clear 
        # the time. There are too many possibilities otherwise. 
        # Tell me a use case that isn't covered, and I'll add it.
        
        line.played_at = None
        line.save()
        
        return render_to_response('on_air/changed_times.json', {'list':[line]}, content_type="application/json")

@auth.decorators.permission_required('on_air.change_playlist', login_url=LOGIN_URL)
def delete(request):
    # easy
    if request.method == "POST" and request.POST['id']:
        id = request.POST['id'];
        models.Playlist.objects.filter(pk=id).delete()
        return HttpResponse('%s' % id)

@auth.decorators.permission_required('on_air.change_playlist', login_url=LOGIN_URL)
def insert(request):
    # almost as easy
    if request.method == "POST" and request.POST['id']:
        id = request.POST['id']
        order = models.Playlist.objects.get(pk=id).order
        try:
            # Split between this order and the next
            order = (order + models.Playlist.objects.filter(order__gt=order).order_by('order')[0].order) / 2
        except IndexError:
            order += 1
        line = models.Playlist(order=order)
        line.save()
        line = models.Playlist.objects.get(pk=line.id)
        return render_to_response('on_air/playlist_line.html', {'line':line})

@auth.decorators.permission_required('on_air.change_playlist', login_url=LOGIN_URL)
def change(request):
    if request.method == "POST":
        if request.POST.get('line'):
            id = int(request.POST['line'])
            line = models.Playlist.objects.get(pk=id)
        else:
            # No id? Get the next blank line
            last_line_played = models.Playlist.objects.filter(played_at__isnull=False).order_by('-order')
            if last_line_played.count() > 0:
                last_line_played = last_line_played[0]
                line = models.Playlist.objects.filter(order__gt=last_line_played.order, song__isnull=True).order_by('order')[0]
            else: 
                line = models.Playlist.objects.filter(song__isnull=True).order_by('order')[0]
            id = line.id
        
        if request.POST.get('song_id'):
            song_id = int(request.POST['song_id'])
            line.song_id = song_id
            line.save()
            
            return render_to_response('on_air/changed_song.json', {'id':id, 'song':line.song}, content_type="application/json")
            
        if request.POST.get('artist') and request.POST.get('song'):
            try:
                song = models.dj.Song.objects.get(song=request.POST['song'], artist__artist=request.POST['artist'])
            except Exception, e:
                # Not unique. Please try again.
                return HttpResponse('Failure is my middle name! %s {name=%s artist__name=%s}' % (e, request.POST['song'], request.POST['artist']))
            
            line.song = song
            line.save()
            
            return render_to_response('on_air/changed_song.json', {'id':id, 'song':song}, content_type="text/json")
            
        return HttpResponse('Problem! We got POST : %s' % (request.POST,))

def song_list(request):
    # looking up songs for autocomplete.
    artist = request.GET['artist']
    song = request.GET['song']
    
    songs = models.dj.Song.objects.filter(search__contains=extras.ugam(song).lower(), artist__artist__iexact=artist).extra(select={'len':'length(song)'}, order_by=['len'])[:5]
    results = [{'value':s.song, 'id':s.id} for s in songs]
    
    return HttpResponse(json.dumps(results), content_type="text/json")


@auth.decorators.permission_required('on_air.change_playlist', login_url=LOGIN_URL)
@transaction.commit_on_success
def play(request):
    # Much too slow Even the simple case (play the next song) takes .4 sec
    if request.method == "POST" and request.POST['id']:
        id = request.POST['id']
        line = models.Playlist.objects.select_related('song__artist').get(pk=id)
        if not line.song or not line.song.artist:
            return HttpResponse('{}', content_type="application/json")
        line.played_at = line.song.last_played = line.song.artist.last_played = datetime.datetime.now()
        line.save()
        line.song.artist.save()
        line.song.save()
        
        # Make sure everything in the future has no time
        cleared = models.Playlist.objects.filter(played_at__isnull=False, order__gt=line.order)
        if cleared.count() > 0:
            # Done this way to only have one update query
            for c in cleared:
                c.played_at = None
            c = list(cleared)
            cleared.update(played_at = None)
            cleared = c
        else:
            cleared = [] # Added to keep from processing this queryset again
    
        # Fill in the recent past
        try:
            prev = models.Playlist.objects.filter(order__lt=line.order, played_at__isnull=False).order_by('-order')[0]
            added = models.Playlist.objects.select_related('song__artist').filter(order__lt=line.order, order__gt=prev.order)
            list(added)
            time_between = (line.played_at - prev.played_at) / (added.count() + 1)
            time = prev.played_at
            for a in added:
                time += time_between
                if a.song and a.song.artist:
                    a.played_at = a.song.last_played = a.song.artist.last_played = time
                    a.save()
                    a.song.artist.save()
                    a.song.save()
        except IndexError:
            # no [0] because empty prev QuerySet
            added = []
        
        return render_to_response('on_air/changed_times.json', {'list':([line]+list(cleared)+list(added))}, content_type="application/json")


# These are called in a seperate window
def search(request):
    """Returns a list view only if there is more than one result."""
    s_for = request.GET['for']
    s_value = request.GET['value'].strip()
    
    if s_for == 'artist':
        results = models.dj.Artist.objects.filter(search__contains=extras.ugam(s_value).lower())
        if results.count() > 1:
            return render_to_response('on_air/search/artist.html', {'artist_list':results, 'for':s_for, 'value':s_value})
        if results.count() == 1:
            return HttpResponseRedirect(reverse("on_air.views.artist", kwargs={"id":results[0].id}))
    
    if s_for == 'album':
        results = models.dj.Album.objects.filter(search__contains=extras.ugam(s_value).lower()).select_related('artist')
        if results.count() > 1:
            return render_to_response('on_air/search/album.html', {'album_list':results, 'for':s_for, 'value':s_value})
        if results.count() == 1:
            return HttpResponseRedirect(reverse("on_air.views.album", kwargs={"id":results[0].id}))
        
        
    if s_for == 'location':
        results = models.dj.Album.objects.filter(location__icontains=s_value).select_related('artist').order_by('location')
        if results.count() > 1:
            return render_to_response('on_air/search/album.html', {'album_list':results, 'for':s_for, 'value':s_value})
        if results.count() == 1:
            return HttpResponseRedirect(reverse("on_air.views.album", kwargs={"id":results[0].id}))
        
        
    if s_for == 'song':
        results = models.dj.Song.objects.filter(search__contains=extras.ugam(s_value).lower(), rating__gt = 0).select_related('artist', 'album').order_by('song')
        if results.count() >= 1:
            return render_to_response('on_air/search/song.html', {'song_list':results, 'for':s_for, 'value':s_value})
        
        
    if s_for == 'label':
        results = models.dj.Album.objects.filter(label__icontains=s_value).select_related('artist').order_by('label')
        if results.count() > 1:
            return render_to_response('on_air/search/album.html', {'album_list':results, 'for':s_for, 'value':s_value})
        if results.count() == 1:
            return HttpResponseRedirect(reverse("on_air.views.album", kwargs={"id":results[0].id}))
        
    # If there is no search term or no results, 404
    return render_to_response('on_air/search/empty.html', {'for':s_for, 'value':s_value})
    

def artist(request, id):
    artist = get_object_or_404(models.dj.Artist, pk=id)
    if request.GET.get('show') == 'songs':
        request.session['artist_view'] = 'all_songs'
    elif request.GET.get('show') == 'albums':
        request.session['artist_view'] = 'albums'
    
    if request.session.get('artist_view') == 'all_songs':
        songs = artist.all_songs.filter(rating__gt = 0)
        return render_to_response('on_air/artist_songs.html', {'artist': artist, 'songs': songs})
    
    albums = artist.album_set.all()
    songs = artist.comp_songs.filter(rating__gt = 0)
    return render_to_response('on_air/artist_albums.html', {'artist': artist, 'albums': albums, 'songs': songs})
    

def album(request, id):
    album = get_object_or_404(models.dj.Album, pk=id)
    song_form = forms.MiniSong(initial={'album':album.id})
    songs = album.song_set.filter(rating__gt=0)
    return render_to_response('on_air/album.html', {'album': album, 'song_form': song_form, 'songs': songs})

@auth.decorators.permission_required('djpro.add_album', login_url=LOGIN_URL)
def album_new(request):
    if request.method == 'POST':
        album_form = forms.Album(request.POST)
        
        if album_form.is_valid():
            album = album_form.save(commit=False)
            song_forms = forms.SongSet(request.POST, instance=album)
            
            if song_forms.is_valid():
                album.save()
                song_forms.save()
                
                return HttpResponseRedirect(reverse('on_air.views.album', kwargs = {'id': album.id}))
                
        else: # get the songs in a form w/o the album
            song_forms = forms.SongSet(request.POST)
    
    else: # GET
        album_form = forms.Album(initial={'artist': request.GET.get('artist')})
        song_forms = forms.SongSet()
        
    return render_to_response('on_air/album_edit.html', {'album': album_form, 'song_set': song_forms}, context_instance=RequestContext(request))

def concerts(request):
    concerts = models.dj.Concert.objects.all();
    return render_to_response('on_air/concerts.html', {'concerts':concerts})

@auth.decorators.permission_required('djpro.add_song', login_url=LOGIN_URL)
def add_song(request):
    """Add a new song straight from the album view by the power of AJAX."""
    song_form = forms.MiniSong(request.POST)
    
    if song_form.is_valid():
        return render_to_response('on_air/song.html', {'song':song_form.save()})
    else:
        return HttpResponse(song_form.errors.as_text(), content_type='text/plain')
    
@csrf_exempt
def tune_tracker_add(request):
    """
    Method used by Tune Tracker to automaticaly update the playlist.

    Tune tracker adds a song to the playlist in the next (empty?) slot and
    automatically plays it.

    request.POST has the artist and song name. All the rest is up to us.
    """
    now = datetime.datetime.now()
    song_name = extras.ugam(request.POST['song'].strip().lower())
    artist = extras.ugam(request.POST['artist'].strip().lower())

    song = models.dj.Song.objects.filter(artist__search=artist, search=song_name, rating__gte=0)[0]

    try:
        # Add to current playlist
        last_played = models.Playlist.objects.filter(played_at__isnull=False).order_by('-order')[0]
        order = last_played.order
        try:
            next_line = models.Playlist.objects.filter(song__isnull=True, order__gt=order).order_by('order')[0]
        except IndexError:
            next_line = models.Playlist(order=order+3)
        next_line.song = song
        next_line.played_at = now
        next_line.save()

        models.TuneTrackerLog(playlist=next_line).save()
    except IndexError:
        # Add to play history
        models.PlayHistory(song=song, played_at=now).save()
        # No need to add to playlist
        
    return HttpResponse('OK', content_type='text/plain')

@auth.decorators.permission_required('on_air.change_playlist', login_url=LOGIN_URL)
def tune_tracker_update(request):
    """Show the TunTracker changes to the DJ"""
    logs = models.TuneTrackerLog.objects.all().select_related('playlist__song__artist', 'playlist__song__album')
    lines = []
    for log in logs:
        lines.append(log.playlist)
        log.delete()
    return render_to_response('on_air/tune_tracker_logs.json', {'logs':lines}, content_type='application/json')


