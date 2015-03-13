from on_air import models, forms
from djpro import ajax

from django.db.models import Count
from django.conf.urls import patterns
from django.contrib import admin
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect

import datetime

class RotationScheduleAdmin(admin.ModelAdmin):
    # we want one page where we can edit the entire schedule at once. Since 
    # each entry only has one editable field, that's not too hard.
    list_display = 'order', 'rotation'
    list_editable = 'rotation',
    list_per_page = 800
    
    actions_on_bottom = True
    
    def add_view(self, request, **kwargs):
        models.RotationSchedule().save()
        return HttpResponseRedirect(reverse(self.admin_site.name + ':on_air_rotationschedule_changelist', current_app="admin"))
    
    #add extra data to the list view
    change_list_template = 'on_air/admin/rotation_schedule_change_list.html'
    def changelist_view(self, request, extra_context=None):
        if (extra_context == None): 
            extra_context = {}
        extra_context['rotation'] = models.dj.Rotation.objects.all()
        return super(RotationScheduleAdmin, self).changelist_view(request, extra_context)

admin.site.register(models.RotationSchedule, RotationScheduleAdmin)


class Top10AlbumsForm(forms.forms.ModelForm):
    album = ajax.AlbumField(label="Album")
    rank = forms.forms.CharField(label=u"New Rank")
    
    class Media:
        js = ('jquery.js', 'jquery-ui.js', 'on_air/top-10-order.js')

class Top10AlbumsInline(admin.TabularInline):
    model = models.Top10Album
    form = Top10AlbumsForm
    extra = 10
    can_delete = True
    fields = ('rank', 'album')
    
    verbose_name_plural="Albums: Drag and drop to reorder"

class Top10Admin(admin.ModelAdmin):
    date_hierarchy = 'week_ending'
    inlines = (Top10AlbumsInline,)
    
    change_list_template = "on_air/admin/top10_change_list.html"
    
    def get_urls(self):
        urls = super(Top10Admin, self).get_urls()
        my_urls = patterns('', 
            (r'^add_this_week/$', self.admin_site.admin_view(self.this_week))
        )
        return my_urls+urls
 
    def this_week(self, request, *args, **kwargs):
        """
        Creates a pre-poulated Top 10 List with the most popular albums 
        of the past week.
        """
        if models.Top10.objects.filter(week_ending = datetime.date.today()).exists():
            id = models.Top10.objects.get(week_ending = datetime.date.today()).id
            return HttpResponseRedirect(reverse(self.admin_site.name + ':on_air_top10_change', args=(id,), current_app="admin"))
        
        obj = models.Top10(week_ending= datetime.date.today())
        obj.save()
        
        since = datetime.date.today() - datetime.timedelta(8)
        albums = models.dj.Album.objects. \
            filter(song__playhistory__played_at__gt = since). \
            annotate(count = Count('song__playhistory')). \
            filter(count__gt = 2).order_by('-count')
        
        rank = 0
        for a in albums:
            rank += 1
            tta = models.Top10Album(album=a, rank=rank, week=obj, count=a.count)
            tta.save()
        
        return HttpResponseRedirect(reverse(self.admin_site.name + ':on_air_top10_change', args=(obj.pk,), current_app="admin"))
                
admin.site.register(models.Top10, Top10Admin)

