from django.contrib import admin, messages
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
from django.urls import reverse, path
from django.shortcuts import render, redirect
from django.conf import settings
from django import forms

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
from .models import SeeAlso, EntryMedia, EntryPurpose, LibraryPersona, WebLink
from .models import Tonality, Material, Ensemble
from .models import Asset, AssetType, AssetCondition, AssetMaker, AssetModel
from .models import Task, TaskStatus, TaskItem, TaskNote
from .models import Folder, FolderItem

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
    
class WebLinkAdmin(admin.TabularInline):
    model = WebLink
    extra = 1
    fk_name = 'entry'
    

class MediaInlineFormSet(forms.BaseInlineFormSet):
   def clean(self):
      super().clean()
      thumbcount = 0      
      for form in self.forms:
         if not form.is_valid():
            return #other errors exist, so don't bother
         if form.cleaned_data and not form.cleaned_data.get('DELETE') and form.cleaned_data['asthumb']:
            thumbcount += 1
      if thumbcount > 1:
          raise forms.ValidationError("Only one advert allowed")
          
    
class MediaAdmin(admin.TabularInline):
    model = EntryMedia
    formset = MediaInlineFormSet
    extra = 1
    

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
    
class CsvImportForm(forms.Form):
    csv_file = forms.FileField()

class EntryAdmin(admin.ModelAdmin, ExportCsvMixin):
    list_display = ('title', 'genre', 'category', 'callno_format', 'composer', 'arranger', 'source', 'publisher', 'pubname', 'pubyear', 'estdecade', 'pagecount', 'condition', 'platecode', 'image_present','instrument','key','completeness' )
    list_filter = ('category', 'genre','saleable', 'composer__country', 'completeness__usable', 'duplicate', 'completeness', ('key', admin.RelatedOnlyFieldListFilter), 'source', EmptyMediaFilter, ('provider', admin.RelatedOnlyFieldListFilter))
    search_fields = ['title', 'composer__given', 'composer__surname', 'arranger__surname','callno','comments', 'composer__realname__surname', 'arranger__realname__surname']
    readonly_fields = ('image_link', 'image_present')
    save_on_top = True
    fields = (('title','saleable','fee'), ('category', 'callno'), ('genre','ensemble', 'key','duration'),'composer', 'arranger', ('publisher', 'pubyear', 'estdecade', 'platecode'), ('pubname', 'pubissue'), ('source','provider'), 'instrument', ('comments','backpage','perfnotes'), ('material','condition','completeness', 'duplicate'), 'image_link')
    autocomplete_fields = ['composer','arranger','provider']
    actions = ["export_as_csv"]
    inlines = [ MediaAdmin, SeeAlsoAdmin, WebLinkAdmin ]
    
    

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
    
    def callno_format(self, instance):
        return "%.8g" % instance.callno
    
    callno_format.admin_order_field = 'callno'
    callno_format.short_description = 'Label'
        
    
    def import_csv(self, request):
        from io import StringIO
        import decimal
        if request.method == "POST":
            if getattr(settings, 'CSV_DEBUG', False):
                messages.set_level(request, messages.DEBUG)
            csv_file = request.FILES["csv_file"]
            fp = StringIO(csv_file.read().decode('utf-8'))
#file_content = list(csv.reader(fp, delimiter=';', quotechar='"'))
            dataReader = csv.reader(fp)
            catcache = {}
            enscache = {}
            entrylist = []
            defcomplete = Completeness.objects.filter(label='Complete').first()
            # Create Entry objects from passed in data
            # ...
            # ID, Cat, Title, Label, Ensemble, Duration, Composer, Arranger, Force
            rowno = 0
            errors = 0
            for prow in dataReader:
                rowno += 1
                error_log("ENTRY LINE %d: %s" % (rowno, str(prow)))
                
                # prow[0] is the internal ID of the entry - evebtually use it as an updater
                self.message_user(request, "ENTRY LINE: %s" % str(prow), messages.DEBUG)
                if rowno == 1:
                    self.message_user(request, "SKIP HEADER")
                    continue
                self.message_user(request, "CHECK CAT: %s" % str(prow[1]))
                if prow[1] not in catcache:
                    category = Category.objects.filter(code__exact=prow[1]).first()
                    error_log("Entry CAT: %s" % str(category))
                    self.message_user(request,"Entry CAT: %s" % str(category), messages.DEBUG)
                    if category:
                        catcache[prow[1]] = category
                    else:
                        self.message_user(request,"Entry CAT: %s NOT FOUND" % str(prow[1]), messages.ERROR)
                        errors += 1
                        continue
                else:
                    self.message_user(request,"Entry CAT: %s HIT" % str(prow[1]), messages.DEBUG)
                    category = catcache[prow[1]]
                
                self.message_user(request, "CHECK ENSE: %s" % str(prow[4]), messages.DEBUG)
                if prow[4].lower() not in enscache:
                    ensemble = Ensemble.objects.filter(name__iexact=prow[4]).first()
                    self.message_user(request,"Entry ENSEMBLE: %s => %s" % (prow[4], str(ensemble)), messages.DEBUG)
                    if ensemble:
                        enscache[prow[4].lower()] = ensemble
                    else:
                        self.message_user(request,"Entry ENSEMBLE: %s NOT FOUND" % str(prow[4]), messages.ERROR)
                        errors += 1
                        continue
                else:
                    self.message_user(request,"Entry ENSEMBLE: %s HIT" % str(prow[4]), messages.DEBUG)
                    ensemble = enscache[prow[4].lower()]
                    
                force = len(prow) >= 9 and prow[8]
                
                
                
                title = ' '.join(prow[2].split())
                title = ', '.join(title.split(','))
                label_str = ' '.join(prow[3].split())
                label = decimal.Decimal(label_str)
                
                previous = Entry.objects.filter(category=category, callno=label).first()
                
                if previous and not force:
                    self.message_user(request,"Existing entry: %s" % str(previous), messages.ERROR)
                    errors += 1
                    continue

                duration = prow[5]
                composer = prow[6].split(',')
                arranger = prow[7].split(',')
                
                composer = Author.find(composer)
                arranger = Author.find(arranger)
                if composer:
                    self.message_user(request,"Found composer: %s" % str(composer), messages.DEBUG)
                    
                if arranger:
                    self.message_user(request,"Found arranger: %s" % str(arranger), messages.DEBUG)
                    
                if not previous:
                    newentry = Entry(
                        category=category,
                        callno=label,
                        title=title,
                        ensemble=ensemble,
                        duration=duration,
                        composer=composer,
                        arranger=arranger,
                        completeness=defcomplete
                        )
                    self.message_user(request, "New Entry: %s" % str(newentry))
                
                    entrylist.append(newentry)
                else:
                    self.message_user(request, "Replace Entry: %s" % str(previous))
                    previous.category = category
                    previous.callno=prow[3]
                    previous.title=title
                    previous.ensemble=ensemble
                    previous.duration=duration
                    previous.composer=composer
                    previous.arranger=arranger
                    previous.completeness=defcomplete
                    entrylist.append(previous)
                
            if errors == 0:
                for eee in entrylist:
                    eee.save()
                    
                self.message_user(request, "Your csv file has been imported")
            else:
                self.message_user(request, "%d errors: no import" % errors, messages.ERROR)
            return redirect(".")
#                return redirect("..")
        form = CsvImportForm()
        payload = {"form": form}
        return render(
            request, "admin/csv_form.twig", payload
        )
    
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
            path('import-csv/', self.import_csv),
        ]
        return my_urls + urls

    def image_link(self, instance):
        error_log("IMAGE LINK: %s %s" % (str(instance.media), str(instance.id)))
        if instance.media:
            return mark_safe('<img width="300" src="%s" alt="%s" />' % ("/library/incipit/" + str(instance.id), "FRED"))
        else:
            return 'MISSING'


    image_link.short_description = "Advert"

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
    readonly_fields = ['item_duration']
    formfield_overrides = {
        models.TextField: {'widget': Textarea(
                           attrs={'rows': 2,
                                  'cols': 40,
                                  })},
    }
    
    def item_duration(self, instance):
        if instance.item:
            return instance.item.duration
        else:
            return "n/a"

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
    formfield_overrides = {
        models.TextField: {'widget': Textarea(
                           attrs={'rows': 1,
                                  'cols': 70,
                                  'style': 'height: 1.25em;'})},
    }


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
    

class FolderFormSet(forms.BaseInlineFormSet):
        
    def clean(self):
        cleaned_data = super().clean()
        scount = {}
        errors = []
        for form in self.forms:
            if not form.cleaned_data:
                continue
            error_log("FOLDER CLEAN SLOTS %s -> %s" % (str(form.instance), str(form.cleaned_data)))
            if form.cleaned_data['position'] in scount:
                errors.append("Duplicate position %s" % str(form.cleaned_data['position']))
            else:
                scount[form.cleaned_data['position']] = 1
                
        if errors:
            raise forms.ValidationError(",".join(errors))
        
        return cleaned_data
        """
        slots = self.slots.all()
        scount = {}
        errors = []
        error_log("FOLDER CLEAN SLOTS %s" % str(slots))
        for slot in slots:
            error_log("FOLDER CLEAN %s" % str(slot))
            if slot.position in scount:
                errors.append("Duplicate position %s" % str(slot.position))
            else:
                scount[slot.position] = 1
        
        if errors:
            raise ValidationError(",".join(errors))
            """

    
class FolderItemAdmin(admin.TabularInline):
    model = FolderItem
    fields = ('position','entry','genre', 'location', 'comment','version')
    readonly_fields = ('genre', 'location')
    extra = 1
    formset = FolderFormSet
    autocomplete_fields = ['entry']
    ordering = ['position']
    formfield_overrides = {
        models.TextField: {'widget': Textarea(
                           attrs={'rows': 2,
                                  'cols': 40,
                                  'style': 'height: 2em;'})},
    }
    
    def genre(self, instance):
        if instance.entry:
            return instance.entry.genre
        else:
            return ""
        
    def location(self, instance):
        if instance.entry:
            return "%s%s" % (str(instance.entry.category.code), str(instance.entry.callno))
        else:
            return ""
        
    
    def get_max_num(self, request, obj):
        if obj:
            error_log("FOLDER GET MAX NUM %s -> %s -> %d" % (str(self), str(obj), obj.slot_count))
            return obj.slot_count
        else:
            return 35
        
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('entry', 'entry__category', 'entry__genre', 'entry__composer')  # no existing records will appear
    
class FolderAdmin(admin.ModelAdmin):
    list_display = ('label','slot_count')
    save_on_top = True
    inlines = [ FolderItemAdmin  ]

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
    
    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        return queryset.select_related('content_type', 'user')  # no existing records will appear


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
admin.site.register(Ensemble)
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
admin.site.register(LibraryPersona)
admin.site.register(EntryPurpose)
#admin.site.register(SeeAlso, SeeAlsoAdmin)
admin.site.register(Folder, FolderAdmin)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(LogEntry, LogEntryAdmin)