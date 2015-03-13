from django.conf.urls import patterns, include, url
from django.contrib.auth import views as auth


urlpatterns = patterns( 'on_air.views',
    (r'^$', 'onair'),
    (r'logout/$', auth.logout, {'next_page':'/djpro/onair/'}),
    
    # Ajax calls
    (r'^delete/$', 'delete'),
    (r'^insert/$', 'insert'),
    (r'^move/$', 'move'),
    (r'^play/$', 'play'),
    (r'^change/$', 'change'),
    (r'^song-list/$', 'song_list'),
    (r'^tune_tracker_update/$', 'tune_tracker_update'),
    
    # seperate window calls
    (r'^search/$', 'search'),
    (r'^artist/(?P<id>\d+)/', 'artist'),
    (r'^album/(?P<id>\d+)/', 'album'),
    (r'^album/new/', 'album_new'),
    (r'^add_song/', 'add_song'),
    (r'^concerts/$', 'concerts'),
)