# coding=utf-8
from djpro import models, forms, ajax
from django.contrib import admin

from django import template
from django.shortcuts import render_to_response
from django.conf.urls import patterns
from django.http import Http404, HttpResponseRedirect
from django.core.exceptions import PermissionDenied, ValidationError

class FindOtherArtistForm(forms.forms.Form):
    # I want to find a way to make this *not* return the current 
    # artist.
    entry = ajax.ArtistField()

class ArtistAdmin(admin.ModelAdmin):
    fields = ('artist', 'info', 'url', 'last_played', 'times_played')
    readonly_fields = ('last_played', 'times_played')
    
    search_fields = ('artist',)
    
    actions = None
    
    # Custom change form template just to change “Delete” into 
    # “Merge with duplicate”. If you aren’t running Django 1.2, 
    # you’ll probably need to update it.
    change_form_template = 'djpro/admin/change_form.html'
    
    def delete_view(self, request, object_id, extra_content=None):
        """Actually a “merge with duplicate” function. Kept the 
        name and most of the code."""
        opts = self.model._meta
        obj = self.get_object(request, object_id)
        errors = []
        
        if not self.has_delete_permission(request, obj):
            raise PermissionDenied
        
        if obj is None:
            raise Http404('%(name)s object with primary key %(key)s does not exist.' % {'name': unicode(opts.verbose_name), 'key': object_id})
        
        # Get all of the objects to be adjusted and check that 
        # we can alter them.
        rels = opts.get_all_related_objects()
        rel_obj = []
        lacking_perms = []
        for r in rels:
            count = getattr(obj, r.get_accessor_name()).all().count()
            if count == 0:
                continue
            if count == 1:
                rel_obj.append(u"%d %s will change its %s" % (count, r.model._meta.verbose_name, r.field.verbose_name))
            else:
                rel_obj.append(u"%d %s will change their %s" % (count, r.model._meta.verbose_name_plural, r.field.verbose_name))
            # Per object perms not avalable yet.
            if not request.user.has_perm(r.model._meta.app_label + '.' + r.model._meta.get_change_permission()):
                lacking_perms.append(r.name)
        
        
        if request.POST: 
            if lacking_perms:
                raise PermissionDenied
            
            form = FindOtherArtistForm(request.POST)
            
            if form.errors:
                errors = form.errors
            else:
                new_obj = form.cleaned_data['entry']
                if new_obj.pk == obj.pk:
                    errors = "You can't merge something with itself."
                else:
                        
                    # move everything over
                    for r in rels:
                        getattr(obj, r.get_accessor_name()).all().update(**{r.field.name : new_obj})
                    # copy artist info. 
                    if not new_obj.last_played or \
                        (obj.last_played and \
                        new_obj.last_played < obj.last_played):
                            new_obj.last_played = obj.last_played
                    if not new_obj.url:
                        new_obj.url = obj.url
                    new_obj.times_played += obj.times_played
                    new_obj.info = "%s\n%s" % (new_obj.info, obj.info)
                    
                    new_obj.save()
                    
                    self.log_deletion(request, obj, unicode(obj))
                    obj.delete()
            
                    self.message_user(request, u'The %(name)s "%(obj)s" was merged with "%(new)s" successfully.' % {'name': unicode(opts.verbose_name), 'obj': unicode(obj), 'new': unicode(new_obj)})
            
                    return HttpResponseRedirect("../../")
        else:
            form = FindOtherArtistForm()
        
        context = {
            "title": "Choose the other artist.",
            "object_name": unicode(opts.verbose_name),
            "object": obj,
            "form": form,
            "errors": errors,
            "media": unicode(form.media),
            "affected": rel_obj,
            "lacking_perms": lacking_perms,
            "opts": opts,
            "app_label": opts.app_label,
        }
        context.update(extra_content or {})
        context_instance = template.RequestContext(request, current_app=self.admin_site.name)
        return render_to_response("djpro/admin/merge_confirmation.html", context, context_instance=context_instance)
    
admin.site.register(models.Artist, ArtistAdmin)



class FilterByRotation(admin.SimpleListFilter):
    """
    Filter to show only albums with at least one song in rotation.
    """
    title = u"In rotation"
    parameter_name = "rotation"

    def lookups(self, request, model_admin):
        return (
                ('Y', u"Yes"),
                ('N', u"No")
               )

    def queryset(self, request, queryset):
        if self.value() == 'Y':
            return queryset.filter(song__rotation__isnull=False).distinct()
        if self.value() == 'N':
            return queryset.exclude(song__rotation__isnull=False).distinct()
        return queryset


class SongForm(forms.forms.ModelForm):
    class Meta:
        model = models.Song
    
    comp_artist = ajax.ArtistField(required=False, label=u'Artist')

class SongInline(admin.TabularInline):
    form = SongForm
    fields = ('song', 'comp_artist', 'track', 'ramp', 'post', 'tempo', 'rating', 'rotation', 'last_played', 'times_played')
    readonly_fields = ('last_played', 'times_played')
    model = models.Song
    extra = 3
    can_delete = True
    formset = forms.SongSet
    

class FindOtherAlbumForm(forms.forms.Form):
    entry = ajax.AlbumField()

class AlbumAdmin(admin.ModelAdmin):
    form = forms.Album
    
    list_display = ('album', 'artist', 'location', 'label', 'year')
    search_fields = ('album',)
    list_filter = (FilterByRotation,)
    
    inlines = (SongInline,)
    
    actions = None
    
    # Custom change form template just to change “Delete” into 
    # “Merge with duplicate”. If you aren’t running Django 1.2, 
    # you’ll probably need to update it.
    change_form_template = 'djpro/admin/change_form.html'

    def delete_view(self, request, object_id, extra_content=None):
        """Actually a “merge with duplicate” function. Kept the name and 
        much of the code."""
        opts = self.model._meta
        obj = self.get_object(request, object_id)
    
        if not self.has_delete_permission(request, obj):
            raise PermissionDenied
    
        if obj is None:
            raise Http404('%(name)s object with primary key %(key)s does not exist.' % {'name': unicode(opts.verbose_name), 'key': object_id})
    
        # Get all of the objects to be adjusted and check that 
        # we can alter them.
        rels = opts.get_all_related_objects()
        rel_obj = []
        lacking_perms = []
        for r in rels:
            count = getattr(obj, r.get_accessor_name()).all().count()
            if count == 0:
                continue
            if count == 1:
                rel_obj.append(u"%d %s will change its %s" % (count, r.model._meta.verbose_name, r.field.verbose_name))
            else:
                rel_obj.append(u"%d %s will change their %s" % (count, r.model._meta.verbose_name_plural, r.field.verbose_name))
            # Per object perms not avalable yet.
            if not request.user.has_perm(r.model._meta.app_label + '.' + r.model._meta.get_change_permission()):
                lacking_perms.append(r.name)
    
        errors = []
    
        if request.POST: 
            if lacking_perms:
                raise PermissionDenied
        
            form = FindOtherAlbumForm(request.POST)
            print(request.POST)
        
            if form.errors:
                errors = form.errors
            else:
                new_obj = form.cleaned_data['entry']
                if new_obj.pk == obj.pk:
                    errors = ["You can't merge something with itself."]
                else:
                    
                    # move everything over
                    for r in rels:
                        getattr(obj, r.get_accessor_name()).all().update(**{r.field.name : new_obj})
                    # copy album info. 
                    new_obj.review = "%s\n%s" % (new_obj.review, obj.review)
                    if new_obj.location == u"NIL":
                        new_obj.location = obj.location
                    elif obj.location not in new_obj.location and obj.location != u"NIL":
                        new_obj.location += ", %s" % obj.location
                
                    new_obj.save()
                
                    self.log_deletion(request, obj, unicode(obj))
                    obj.delete()
        
                    self.message_user(request, 'The %(name)s "%(obj)s" was merged with "%(new)s" successfully.' % {'name': unicode(opts.verbose_name), 'obj': unicode(obj), 'new': unicode(new_obj)})
        
                    return HttpResponseRedirect("../../")
        else:
            form = FindOtherAlbumForm()
    
        context = {
            "title": "Choose the other album.",
            "object_name": unicode(opts.verbose_name),
            "object": obj,
            "form": form,
            "errors": errors,
            "media": unicode(form.media),
            "affected": rel_obj,
            "lacking_perms": lacking_perms,
            "opts": opts,
            "app_label": opts.app_label,
        }
        context.update(extra_content or {})
        context_instance = template.RequestContext(request, current_app=self.admin_site.name)
        return render_to_response("djpro/admin/merge_confirmation.html", context, context_instance=context_instance)
    
admin.site.register(models.Album, AlbumAdmin)


class RotationOnlyForm(forms.forms.ModelForm):
    class Meta:
        model = models.Song
        fields = ('rotation', )

class RotationSongFormSet(forms.forms.models.BaseModelFormSet):
    form = RotationOnlyForm
    model = models.Song
    extra = 0
    can_delete = True
    can_order = False
    max_num = None
    absolute_max = 200
    
    def add_fields(self, form, i):
        super(RotationSongFormSet, self).add_fields(form, i)
        if not form.instance.can_delete():
            form.fields['DELETE'].widget = forms.forms.HiddenInput()
            form.fields['DELETE'].clean = lambda a: False


class RotationAdmin(admin.ModelAdmin):
    list_display = ('rotation', 'max', 'admin_song_count')
    
    def admin_song_count(self, obj):
        return u"%d <a href=\"songs/\">(Edit songs)</a>" % obj.song_set.all().count()
    admin_song_count.short_description = u"Number of songs"
    admin_song_count.allow_tags = True
    
    def get_urls(self):
        urls = super(RotationAdmin, self).get_urls()
        my_urls = patterns('', 
            (r'^songs/$', self.admin_site.admin_view(self.changesongs))
        )
        return my_urls+urls
        
    def changesongs(self, request):
        if request.POST:
            form = RotationSongFormSet(request.POST, queryset=models.Song.objects.filter(rotation__isnull=False).select_related('rotation', 'artist', 'album').order_by('rotation__max', 'added_on'))
            
            if form.is_valid():
                form.save()
                return HttpResponseRedirect("../")
        else:
            form = RotationSongFormSet(queryset=models.Song.objects.filter(rotation__isnull=False).select_related('rotation', 'artist', 'album').order_by('rotation__max', 'added_on'))
            
        context = {
            "title" : "Move rotation songs",
            "formset" : form,
            "opts" : self.model._meta,
            "app_label" : self.model._meta.app_label,
            "has_change_permission" : True,
        }
        context_instance = template.RequestContext(request, current_app=self.admin_site.name)
        return render_to_response("djpro/admin/change_rotation_songs.html", context, context_instance)

admin.site.register(models.Rotation, RotationAdmin)


class VenueAdmin(admin.ModelAdmin):
    list_display = ('venue', 'location', 'count_concerts')
    
    def count_concerts(self, obj):
        return obj.concert_set.count()
    count_concerts.short_description = 'Number of concerts'

admin.site.register(models.Venue, VenueAdmin)


class PerformerInline(admin.TabularInline):
    fields = ('order', 'performer',)
    model = models.Performer
    extra = 3

class ConcertAdmin(admin.ModelAdmin):
    form = forms.Concert
    list_display = ('date', 'venue')
    inlines = (PerformerInline,)

admin.site.register(models.Concert, ConcertAdmin)

from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin
 
admin.site.unregister(User)
 
class UserProfileInline(admin.StackedInline):
	model = models.UserProfile
 
class UserProfileAdmin(UserAdmin):
	inlines = [UserProfileInline]
 
admin.site.register(User, UserProfileAdmin)
