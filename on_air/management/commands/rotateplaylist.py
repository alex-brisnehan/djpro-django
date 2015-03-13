import django.db.transaction

class Command(django.core.management.base.NoArgsCommand):
    help = '''Designed to be run as a cron job, this command does three things:

  1. Increment the song's and artist play count for each played song in the playlist.
  2. Moves the played songs from the current playlist to the history
  3. Repopulates the playlist with songs currently in rotation'''
    
    @django.db.transaction.commit_on_success
    def handle_noargs(self, **kwargs):
        import datetime
        from django.contrib.sessions.models import Session
        from on_air import models
        
        # Force everyone to log out
        Session.objects.all().delete()

        # Move the current playlist to the history. 
        # but first, clean it up.
        models.Playlist.objects.filter(song__isnull=True).delete()
        models.Playlist.objects.filter(song__artist__isnull=True).delete()
        models.Playlist.objects.filter(song__rating__lt=-1).delete()
        try:
            last_line = models.Playlist.objects.filter(played_at__isnull=False).order_by('-order')[0].order
            models.Playlist.objects.filter(order__gt=last_line).delete()
            
            # Mark the first one as played (Thank you, Milkman Dan)
            first_line = models.Playlist.objects.order_by('order')[0]
            if first_line.played_at is None:
                date = models.Playlist.objects.filter(played_at__isnull=False).order_by('order')[0].played_at
                # can't use now() because it might be tomorrow.
                first_line.played_at = datetime.datetime(date.year, date.month, date.day, 7, 0) ##Too specific
                first_line.save()
    
            # If there are unplayed gaps, fill them in with simple extrapolations.
            while models.Playlist.objects.filter(played_at__isnull=True).count() > 0:
                unplayed = models.Playlist.objects.filter(played_at__isnull=True)[0]
                start = models.Playlist.objects.filter(played_at__isnull=False, order__lt=unplayed.order).order_by('-order')[0]
                end = models.Playlist.objects.filter(played_at__isnull=False, order__gt=unplayed.order).order_by('order')[0]
        
                unplayed = models.Playlist.objects.filter(order__gt=start.order, order__lt=end.order).all()
                delta = (end.played_at-start.played_at) / (unplayed.count()+1)
                for line in unplayed:
                    line.played_at = start.played_at + delta
                    line.save()
                    start = line
            
            # increment play counts
            for line in models.Playlist.objects.all().select_related('song__artist'):
                line.song.times_played += 1
                line.song.save()
                line.song.artist.times_played += 1
                line.song.artist.save()
            
            # Feed back
            print "%d songs added to the history" % models.Playlist.objects.all().count()
                
            #finally save them in the history
            for line in models.Playlist.objects.all():
                models.PlayHistory(song=line.song, played_at=line.played_at).save()
        
        except IndexError: #There is no object [0], thus no objects
            pass

        models.Playlist.objects.all().delete()

        # Now, build the lists of randomized rotation songs
        rot_songs = dict([(rot.id, rot.song_set.all().order_by('?')) for rot in models.dj.Rotation.objects.all()])
        rot_next = dict([(rot_id, 0) for rot_id in rot_songs.keys()])

        # Rebuild the playlist from the rotation schedule and the random list of songs
        for line in models.RotationSchedule.objects.all():
            rot_id = line.rotation_id
            if rot_id is not None and len(rot_songs[rot_id]) > 0:
                models.Playlist(order=line.order, song=rot_songs[rot_id][rot_next[rot_id]]).save()
                rot_next[rot_id] = (rot_next[rot_id] + 1) % len(rot_songs[rot_id])
            else:
                models.Playlist(order=line.order).save()
        
        #feed back    
        print "%d lines in the playlist" % models.Playlist.objects.all().count()

