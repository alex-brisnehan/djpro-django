from django.conf.urls import patterns, include, url

urlpatterns = patterns( 'front_page.views',
    (r'^playlist/$', 'playlist'),
    (r'^playlist/xml/$', 'playlist_xml'),
    (r'^playlist/current/$', 'current'),
    (r'^concerts/$', 'concert_list'),
    (r'^concerts/Radio 1190 concerts.ics$', 'concert_ical'),
    (r'^top_albums/$', 'top10'),
)
