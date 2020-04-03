from django.contrib import admin
from django.contrib.admin.widgets import AdminFileWidget
from django.db import models
from django.utils.safestring import mark_safe
from django.forms.widgets import Textarea
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Author
from .models import Category
from .models import Entry
from .models import Instrument
from .models import Program
from .models import Country
import sys
from .utilx  import error_log

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

class EntryAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'callno', 'composer', 'arranger', 'image_present', 'duration', 'instrument')
    list_filter = ('category', )
    search_fields = ['title', 'composer__given', 'composer__surname', 'arranger__surname']
    readonly_fields = ('image_link', 'image_present')
    save_on_top = True
    fields = ('title', ('category', 'callno'), ('composer', 'arranger'), 'instrument', 'comments', 'media', 'image_link')
    formfield_overrides = {
        models.TextField: {'widget': Textarea(
              attrs={
                  'rows': 4,
                  'cols': 40
              })
        },
    }

    def image_link(self, instance):
        error_log("IMAGE LINK: %s %s" % (str(instance.media), str(instance.id)))
        if instance.media:
            return mark_safe('<img width="300" src="%s" alt="%s" />' % ("/library/incipit/" + str(instance.id), "FRED"))
        else:
            return 'MISSING'
        
    
    image_link.short_description = "Image Link"
    
    def image_present(self, instance):
        
        return not not instance.media            
        
    
    image_present.short_description = "Image"
    image_present.boolean = True
    
    
    
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('surname', 'given', 'country', 'bornyear', 'diedyear')
    search_fields = ['surname', 'given']

# Define a new User admin
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'first_name', 'last_name', 'is_staff', 'last_login', 'is_superuser')

admin.site.register(Entry, EntryAdmin)
admin.site.register(Author, AuthorAdmin)
admin.site.register(Program)
admin.site.register(Category)
admin.site.register(Instrument)
admin.site.register(Country)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)