from django.contrib import admin

from .models import Entry, Author, Program, Category, Instrument

class EntryAdmin(admin.ModelAdmin):
    list_display = ('title', 'category', 'callno', 'composer', 'arranger', 'duration', 'instrument')
    list_filter = ('category',)
    search_fields = ['title','composer__given', 'composer__surname', 'arranger__surname']
    
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('surname', 'given')
    search_fields = ['surname','given']


admin.site.register(Entry, EntryAdmin)
admin.site.register(Author, AuthorAdmin)
admin.site.register(Program)
admin.site.register(Category)
admin.site.register(Instrument)
