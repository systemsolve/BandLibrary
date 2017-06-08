from django.contrib import admin
from django.contrib.admin.widgets import AdminFileWidget
from django.utils.safestring import mark_safe
import sys
from django.db import models

from .models import Entry, Author, Program, Category, Instrument

class AdminImageWidget(AdminFileWidget):
    def render(self, name, value, attrs=None):
        print >>sys.stderr,"IMAGE WIDGET: %s %s" % (name, str(self))
        output = []
        if value and getattr(value, "url", None):
            image_url = value.name
            file_name = str(value)
            output.append(u' <img src="%s" alt="%s" />' % \
                          (image_url, file_name))
        output.append(super(AdminFileWidget, self).render(name, value, attrs))
        return mark_safe(u''.join(output))

class EntryAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'callno', 'composer', 'arranger', 'image_present', 'duration', 'instrument')
    list_filter = ('category',)
    search_fields = ['title','composer__given', 'composer__surname', 'arranger__surname']
    readonly_fields = ('image_link', 'image_present')

    def image_link(self, instance):
        print >>sys.stderr,"IMAGE LINK: %s %s" % (str(instance.media), str(instance.id))
        if instance.media:
            return mark_safe(u'<img width="300" src="%s" alt="%s" />' % ("/library/incipit/" + str(instance.id), "FRED"))
        else:
            return u'MISSING'
        
    
    image_link.short_description = "Image Link"
    
    def image_present(self, instance):
        
        return not not instance.media            
        
    
    image_present.short_description = "Image"
    image_present.boolean = True
    
    
    
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('surname', 'given')
    search_fields = ['surname','given']


admin.site.register(Entry, EntryAdmin)
admin.site.register(Author, AuthorAdmin)
admin.site.register(Program)
admin.site.register(Category)
admin.site.register(Instrument)
