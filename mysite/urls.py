from django.conf.urls import patterns, include, url
from django.contrib import admin

admin.autodiscover()

urlpatterns = patterns('',
    url(r'^djpro/onair/', include('on_air.urls')),
    url(r'^djpro/', include('djpro.urls')),
    url(r'^playlist/tune_tracker_play/$', 'on_air.views.tune_tracker_add'),
    url(r'^', include('front_page.urls')),

    url(r'^djpro/admin/', include(admin.site.urls)),
)