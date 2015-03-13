# encoding: utf-8
from datetime import date, datetime, timedelta
import re

from django.http import HttpResponse
from django.shortcuts import render_to_response
from django.utils.html import escape

import djpro.models as djpro
import on_air.models as on_air


def playlist(request):
    """
    Returns a list of songs played. If there is no request.GET['day'], then 
    return the playlist for today from Playlist. Otherwise return the day
    from PlayHistory.
    """
    errors = []
    
    # Get the day of the request
    if request.GET.get('day', ''):
        day = request.GET['day']
        try:
            if re.match('[0-9]+/[0-9]+/[0-9]{4}', day):
                today = datetime.strptime(day, '%m/%d/%Y').date()
            elif re.match('[0-9]+/[0-9]+/[0-9]{2}', day):
                today = datetime.strptime(day, '%m/%d/%y').date()
            elif re.match(r'[0-9]+\-[0-9]+\-[0-9]+', day):
                today = datetime.strptime(day, '%Y-%m-%d').date()
            else:
                raise ValueError()
        except ValueError:
            today = date.today()
            errors.append(u"The date “%s” isn’t actually a date." % day)
    
    else:
        today = date.today()
        
    # Get the the day before & after and the playlist for the date.
    if today != date.today():
        # We do this complex lookup because sometimes days get skipped
        yesterday = on_air.PlayHistory.objects.filter(played_at__lt=today).order_by('-played_at')[0:1]
        try:
            yesterday = yesterday.get().played_at.date()
        except on_air.PlayHistory.DoesNotExist:
            yesterday = None
        
        tomorrow = date.fromordinal(today.toordinal()+1)
        tomorrow = on_air.PlayHistory.objects.filter(played_at__gte=tomorrow).order_by('played_at')[0:1]
        try:
            tomorrow = tomorrow.get().played_at.date()
        except on_air.PlayHistory.DoesNotExist:
            tomorrow = None
        
        playlist = on_air.PlayHistory.objects.filter(played_at__gte=today).select_related('song__artist', 'song__album')
        if tomorrow:
            playlist = playlist.filter(played_at__lt=tomorrow)
            
        if playlist.count() == 0:
            errors.append(u"There is no playlist for %d/%d/%d" % (today.month, today.day, today.year))
    else:
        yesterday = on_air.PlayHistory.objects.all().order_by('-played_at')[0].played_at.date()
        tomorrow = None
        
        playlist = on_air.Playlist.objects.filter(played_at__isnull=False).order_by('-played_at').select_related('song__artist', 'song__album')
    
    return render_to_response('front_page/playlist.html', {'list': playlist, 'yesterday': yesterday, 'today': today, 'tomorrow': tomorrow, 'errors': errors})

def playlist_xml(request):
    """
    Retrieves the current playlist as XML. Designed to be used by the smartphone app.
    """
    playlist = on_air.Playlist.objects.filter(played_at__isnull=False).order_by('-played_at').select_related('song__artist', 'song__album')
    
    return render_to_response('front_page/playlist.xml', {'list': playlist}, mimetype="application/xml")

def current(request):
    """Show the last played song as XML for the various parsers"""
    try:
        pl = on_air.Playlist.objects.filter(played_at__gt=datetime.now()-timedelta(seconds=300), song__artist__isnull=False).select_related('song__artist', 'song__album').order_by('-played_at')[0]
        song = pl.song
        artist = pl.song.artist
        album = pl.song.album
    except IndexError:
        song = None
        artist = None
        album = None

    return render_to_response('front_page/current.xml', {'song': song, 'artist':artist, 'album':album}, mimetype='application/xml')

def concert_list(request):
    """Shows the concerts in HTML"""
    concerts = djpro.Concert.objects.all().select_related('venue', 'performer')
    return render_to_response('front_page/concerts.html', {'list': concerts})
    

def concert_ical(request):
    """Shows the concerts in ICalendar format. For use with iPhones."""
    concerts = djpro.Concert.objects.all().select_related('venue', 'performer')
    return render_to_response('front_page/concerts.ics', {'list': concerts}, mimetype="text/calendar")

def top10(request):
    """Shows the top 10 (or top 30) of the week request.GET['week'].
    
    Always shows the nearest top 10 week.
    """
    errors = []
    if request.GET.get('week'):
        day = request.GET['week']
        try:
            if re.match('[0-9]+/[0-9]+/[0-9]{4}', day):
                week = datetime.strptime(day, '%m/%d/%Y').date()
            elif re.match('[0-9]+/[0-9]+/[0-9]{2}', day):
                week = datetime.strptime(day, '%m/%d/%y').date()
            elif re.match(r'[0-9]+\-[0-9]+\-[0-9]+', day):
                week = datetime.strptime(day, '%Y-%m-%d').date()
            else:
                raise ValueError()
        except ValueError:
            week = date.today()
            errors.append(u"The date “%s” isn’t actually a date." % day)
    else:
        week = date.today()
    
    # this_week is the top 10 list in question
    qs = on_air.Top10.objects.filter(week_ending__gte=week).order_by('week_ending')[:2]
    if qs.exists():
        this_week = qs[0]
    else: 
        this_week = on_air.Top10.objects.all().order_by('-week_ending')[0]
    week = this_week.week_ending
    
    # prev and next are dates of top 10 lists
    next = qs[1].week_ending if qs.count() > 1 else None
    prev = on_air.Top10.objects.filter(week_ending__lt=week).order_by('-week_ending')[0:1]
    prev = prev[0].week_ending if prev.exists() else None

    return render_to_response('front_page/top10.html', {'this_week': week, 'next_week': next, 'prev_week': prev, 'list':this_week.albums.all().select_related('album__artist'), 'errors':errors})
    
