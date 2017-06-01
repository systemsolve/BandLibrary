from django.shortcuts import render
from django.http import HttpResponse
from django.utils.safestring import mark_safe
from django.db.models import Q
import django_tables2 as tables
from django_tables2 import RequestConfig
from django_tables2.utils import A  # alias for Accessor
import subprocess, os, sys
from django.conf import settings


from models import Entry, Category

class EntryTable(tables.Table):
    title = tables.LinkColumn('entry', args=[A('pk')])
    media = tables.LinkColumn('entry', args=[A('pk')])
    
    def render_media(self, value, record):
        if value:
            return mark_safe("<img width=40 src='incipit/%s'>" % record.id)
        else:
            return ""

    class Meta:
        model = Entry
        # add class="paleblue" to <table> tag
        attrs = {'class': 'paleblue'}
        exclude = ('id', 'comments')
        sequence = ('title', 'category', 'callno', 'composer', 'arranger', 'instrument', 'media')

def is_number(zz):
    try:
        int(zz)
        return True
    except ValueError:
        return False

def entry(request, item):
    entry = Entry.objects.filter(id__exact=item).first()
    return render(request, 'library/entry.twig', {'entry': entry})


def index(request):
    fff = Q()
    thewords = ""
    thecat = ""
    if 'words' in request.GET:
        www = request.GET['words']
        if www:
            wfilter = (Q(title__icontains=www)|Q(composer__given__icontains=www)|Q(composer__surname__icontains=www))
            fff = fff & wfilter
            thewords = www

    if 'category' in request.GET:
        www = request.GET['category']
        if www and is_number(www):
            cfilter = (Q(category__exact=www))
            fff = fff & cfilter
            thecat = int(www)

    if fff:
        table = EntryTable(Entry.objects.filter(fff))
    else:
        table = EntryTable(Entry.objects.all())
    RequestConfig(request, paginate={'per_page': 50}).configure(table)    
    return render(request, 'library/biglist.twig', {'entries': table, 'categories': Category.objects.all(), 'thewords': thewords, 'thecat': thecat})

#basedir = '/Users/david/src/BandLibrary'
#mediadir = os.path.join(basedir, 'media')
#cachedir = os.path.join(basedir, 'mediacache')
mediadir = settings.BL_MEDIADIR
cachedir = settings.BL_CACHEDIR

def incipit(request, item):
    entry = Entry.objects.filter(pk__exact=item).first()
    try:
        print >>sys.stderr, "open %s" % os.path.join(cachedir, entry.media + ".jpg")
        ffc = open(os.path.join(cachedir, entry.media + ".jpg"))
    except:
        print >>sys.stderr, "convert %s" % os.path.join(mediadir, entry.media)
        subprocess.call("pdftoppm -singlefile -jpeg '%s' '%s'" % (os.path.join(mediadir, entry.media), os.path.join(cachedir, entry.media)), shell=True)
        ffc = open(os.path.join(cachedir, entry.media + ".jpg"))
    return HttpResponse(ffc.read(), content_type="image/jpeg")

def top(request):
    return render(request, 'library/home.twig', {'categories': Category.objects.all()})