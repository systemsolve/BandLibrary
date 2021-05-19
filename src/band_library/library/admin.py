from django.contrib import admin
from django.contrib.admin.widgets import AdminFileWidget
from django.contrib.admin import SimpleListFilter
from django.db import models
from django.db.models import Count, Q
from django.utils.safestring import mark_safe
from django.forms.widgets import Textarea
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User

from django.contrib.admin.models import LogEntry, DELETION
from django.utils.html import escape
from django.urls import reverse

from .models import Author
from .models import Category
from .models import Entry
from .models import Instrument
from .models import Program, ProgramItem
from .models import Country
from .models import Source
from .models import Publisher
from .models import Genre
from .models import Publication
from .models import Condition
from .models import Completeness
from .models import SeeAlso
from .models import Tonality, Material
from .models import Asset, AssetType, AssetCondition, AssetMaker, AssetModel
from .models import Task, TaskStatus, TaskItem, TaskNote
import sys
from .utilx  import error_log

import csv
from django.http import HttpResponse

class ExportCsvMixin:
    def export_as_csv(self, request, queryset):

        meta = self.model._meta
        field_names = [field.name for field in meta.fields]
        field_headings = [(field.verbose_name if field.verbose_name else field.name).capitalize() for field in meta.fields]

        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename={}.csv'.format(meta)
        writer = csv.writer(response)

        writer.writerow(field_headings)
        for obj in queryset:
            row = writer.writerow([getattr(obj, field) for field in field_names])

        return response

    export_as_csv.short_description = "CSV of Selected"

class AdminImageWidget(AdminFileWidget):
    def render(self, name, value, attrs=None):
        error_log("IMAGE WIDGET: %s %s" % (name, str(self)))
        output = []
        if value and getattr(value, "url", None):
            image_url = value.name
            file_name = str(value)
            output.append(' <img src="%s" alt="%s" />' % \
                          (image_url, file_name))
        output.append(super(AdminFileWidget, self).render(name, value, attrs))
        return mark_safe(''.join(output))

class SeeAlsoAdmin(admin.TabularInline):
    model = SeeAlso
    extra = 1
    fk_name = 'source_entry'
    autocomplete_fields = ['entry']


class EmptyMediaFilter(admin.SimpleListFilter):
    title = "Media State"
    parameter_name = "media"

    def lookups(self, request, model_admin):
        return (
            ('1', 'Absent', ),
            ('0', 'Present', ),
        )

    def queryset(self, request, queryset):
        error_log("IMAGE FILTER: %s %s" % (str(request), str(self)))
        if self.value() in ('0', '1'):
            kwargs = { '{0}__isnull'.format(self.parameter_name) : self.value() == '1' }
            if (self.value() == '1'):
                return queryset.filter(Q(media__isnull=True)|Q(media__exact=''))
            else:
                return queryset.filter(media__isnull=False)
        return queryset

class EntryAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = ('title', 'genre', 'category', 'callno', 'composer', 'arranger', 'source', 'publisher', 'pubname', 'pubyear', 'estdecade', 'pagecount', 'condition', 'platecode', 'image_present','instrument','key','completeness' )
    list_filter = ('category', 'genre','composer__country', 'completeness__usable', 'duplicate', 'completeness', ('key', admin.RelatedOnlyFieldListFilter), 'source', EmptyMediaFilter, ('provider', admin.RelatedOnlyFieldListFilter))
    search_fields = ['title', 'composer__given', 'composer__surname', 'arranger__surname','callno','comments', 'composer__realname__surname', 'arranger__realname__surname']
    readonly_fields = ('image_link', 'image_present')
    save_on_top = True
    fields = ('title', ('category', 'callno'), ('genre','key'),'composer', 'arranger', ('publisher', 'pubyear', 'estdecade', 'platecode'), ('pubname', 'pubissue'), ('source','provider'), 'instrument', ('comments','backpage'), 'media',('material','condition','pagecount','incomplete', 'completeness', 'duplicate'), 'image_link', 'digitised')
    autocomplete_fields = ['composer','arranger','provider']
    actions = ["export_as_csv"]
    inlines = [ SeeAlsoAdmin ]

    formfield_overrides = {
        models.TextField: {'widget': Textarea(
              attrs={
                  'rows': 4,
                  'cols': 40
              })
        },
    }

    """
    def get_queryset(self, request):
        qs = super().get_queryset(request)

        qs = qs.annotate(_has_media=Count('compositions', distinct=True),
            _arranger=Count('arrangements', distinct=True),
            _provider=Count('donations', distinct=True))


        #error_log("AUTHOR QS: %s" % qs.query)
        return qs
    """

    def image_link(self, instance):
        error_log("IMAGE LINK: %s %s" % (str(instance.media), str(instance.id)))
        if instance.media:
            return mark_safe('<img width="300" src="%s" alt="%s" />' % ("/library/incipit/" + str(instance.id), "FRED"))
        else:
            return 'MISSING'


    image_link.short_description = "Image Link"

#    def is_complete(self, instance):
#
#        return instance.completeness.usable       # looks strange - ensures a boolean
#
#
#    is_complete.short_description = "Complete?"
#    is_complete.boolean = True

    def image_present(self, instance):

        return not not instance.media       # looks strange - ensures a boolean


    image_present.short_description = "Image"
    image_present.boolean = True
    
class ProgramItemAdmin(admin.TabularInline):
    model = ProgramItem
    extra = 1
    fk_name = 'program'
    autocomplete_fields = ['item']
    formfield_overrides = {
        models.TextField: {'widget': Textarea(
                           attrs={'rows': 2,
                                  'cols': 40,
                                  })},
    }

class ProgramAdmin(admin.ModelAdmin):
    save_on_top = True
    inlines = [ ProgramItemAdmin ]
    
class AssetAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = ('asset_type', 'allocated', 'manufacturer', 'model', 'identifier')
    search_fields = ['asset_type__label', 'model__label']
    list_filter = ('allocated', 'asset_type','manufacturer')
    save_on_top = True
    #autocomplete_fields = ['realname']
    actions = ["export_as_csv"]
    ordering = ('asset_type__label', 'manufacturer__label')
    formfield_overrides = {
        models.TextField: {'widget': Textarea(
              attrs={
                  'rows': 5,
                  'cols': 40
              })
        },
    }
    

class AuthorAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = ('surname', 'given', 'arranger', 'composer', 'provider','country', 'bornyear', 'diedyear','realname')
    search_fields = ['surname', 'given']
    list_filter = ('country',)
    save_on_top = True
    autocomplete_fields = ['realname']
    actions = ["export_as_csv"]
    formfield_overrides = {
        models.TextField: {'widget': Textarea(
              attrs={
                  'rows': 5,
                  'cols': 40
              })
        },
    }

    def get_queryset(self, request):
        qs = super().get_queryset(request)

        qs = qs.annotate(_composer=Count('compositions', distinct=True),
            _arranger=Count('arrangements', distinct=True),
            _provider=Count('donations', distinct=True))


        #error_log("AUTHOR QS: %s" % qs.query)
        return qs


    def composer(self, instance):
        return instance._composer


    def arranger(self, instance):
        return instance._arranger

    def provider(self, instance):
        return instance._provider

    composer.admin_order_field = '_composer'
    arranger.admin_order_field = '_arranger'
    provider.admin_order_field = '_provider'

class TaskItemAdmin(admin.TabularInline):
    model = TaskItem
    extra = 1
    autocomplete_fields = ['entry','asset']


class TaskNoteAdminList(admin.TabularInline):
    model = TaskNote
    extra = 0
    can_delete = False
    readonly_fields = ('description','date')
    
    def has_add_permission(self, request, obj=None):
        return False


class TaskNoteAdminAdd(admin.TabularInline):
    model = TaskNote
    can_delete = False
    verbose_name = "New Notes"
    verbose_name_plural = "New Notes"
    extra = 1
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.none()  # no existing records will appear


class TaskAdmin(admin.ModelAdmin):
    list_display = ('summary','person','extperson', 'status','create_date')
    save_on_top = True
    inlines = [ TaskItemAdmin, TaskNoteAdminList, TaskNoteAdminAdd  ]

# Define a new User admin
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'is_staff', 'last_login', 'is_superuser')


class LogEntryAdmin(admin.ModelAdmin):
    date_hierarchy = 'action_time'

    list_filter = [
        'user',
        'content_type',
        'action_flag'
    ]

    search_fields = [
        'object_repr',
        'change_message'
    ]

    list_display = [
        'action_time',
        'user',
        'content_type',
        'object_link',
        'action_flag',
    ]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def object_link(self, obj):
        if obj.action_flag == DELETION:
            link = escape(obj.object_repr)
        else:
            ct = obj.content_type
            link = '<a href="%s">%s</a>' % (
                reverse('admin:%s_%s_change' % (ct.app_label, ct.model), args=[obj.object_id]),
                escape(obj.object_repr),
            )
        return mark_safe(link)

    object_link.admin_order_field = "object_repr"
    object_link.short_description = "object"


admin.site.register(Entry, EntryAdmin)
admin.site.register(Author, AuthorAdmin)
admin.site.register(Program, ProgramAdmin)
admin.site.register(Category)
admin.site.register(Instrument)
admin.site.register(Country)
admin.site.register(Source)
admin.site.register(Publisher)
admin.site.register(Publication)
admin.site.register(Condition)
admin.site.register(Genre)
admin.site.register(Completeness)
admin.site.register(Tonality)
admin.site.register(Material)
admin.site.register(Asset, AssetAdmin)
admin.site.register(AssetType)
admin.site.register(AssetCondition)
admin.site.register(AssetMaker)
admin.site.register(AssetModel)
admin.site.register(Task, TaskAdmin)
admin.site.register(TaskStatus)
#admin.site.register(SeeAlso, SeeAlsoAdmin)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(LogEntry, LogEntryAdmin)