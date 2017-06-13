import datetime
from django.conf import settings
from django.db.models import Q, IntegerField
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.db.models.functions import Cast
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.safestring import mark_safe
import django_tables2 as tables
from django_tables2 import RequestConfig
from django_tables2.utils import A
from models import Category
from models import Entry
import os
import subprocess
import sys

class EntryTable(tables.Table):
    title = tables.LinkColumn('entry', args=[A('pk')])
    media = tables.LinkColumn('entry', args=[A('pk')])
    
    def render_media(self, value, record):
        if value:
            return mark_safe("<img width=40 src='chip/%s'>" % record.id)
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

@login_required
def entry(request, item):
    entry = Entry.objects.filter(id__exact=item).first()
    return render(request, 'library/entry.twig', {'entry': entry, "can_edit": request.user.is_authenticated and request.user.is_superuser})


@login_required
def index(request):
    fff = Q()
    thewords = ""
    thecat = ""
    entries = Entry.objects
    if 'words' in request.GET:
        www = request.GET['words'].strip()
        if www:
            wfilter = (Q(title__icontains=www) | Q(composer__given__icontains=www) | Q(composer__surname__icontains=www))
            fff = fff & wfilter
            thewords = www

    if 'category' in request.GET:
        www = request.GET['category']
        if www and is_number(www):
            cfilter = (Q(category__exact=www))
            fff = fff & cfilter
            thecat = int(www)

    if fff:
        table = EntryTable(entries.filter(fff))
    else:
        table = EntryTable(entries.all())
    if not request.user.has_module_perms('library'):
        table.exclude = ('id', 'comments', 'callno', 'added', 'duration')
    RequestConfig(request, paginate={'per_page': 50}).configure(table)    
    return render(request, 'library/biglist.twig', {'entries': table, 'categories': Category.objects.all(), 'thewords': thewords, 'thecat': thecat})

#basedir = '/Users/david/src/BandLibrary'
#mediadir = os.path.join(basedir, 'media')
#cachedir = os.path.join(basedir, 'mediacache')
mediadir = settings.BL_MEDIADIR
cachedir = settings.BL_CACHEDIR

@login_required
def incipit(request, item):
    entry = Entry.objects.filter(pk__exact=item).first()
    fname = entry.media.name
    res = ''
    return makeimage(fname, res, "")

@login_required
def chip(request, item):
    entry = Entry.objects.filter(pk__exact=item).first()
    fname = entry.media.name
    res = '-r 16'
    return makeimage(fname, res, "chip-")

def makeimage(fname, res, prefix):
    target = prefix + fname
    try:
        print >> sys.stderr, "open %s" % os.path.join(cachedir, target + ".jpg")
        ffc = open(os.path.join(cachedir, target + ".jpg"))
    except:
        print >> sys.stderr, "convert %s" % os.path.join(mediadir, fname)
        command = "pdftoppm -singlefile %s -jpeg \"%s\" \"%s\"" % (res, os.path.join(mediadir, fname), os.path.join(cachedir, target))
        print >> sys.stderr, "command %s" % command
        subprocess.call(command, shell=True)
        ffc = open(os.path.join(cachedir, target + ".jpg"))
        
    response = HttpResponse(ffc.read(), content_type="image/jpeg")
    response['Cache-Control'] = "public"
    
    modtime = os.path.getmtime(os.path.join(cachedir, target + ".jpg"))
    response['Last-Modified'] = datetime.datetime.utcfromtimestamp(modtime).strftime("%a, %d %b %y %H:%M:%S GMT")
    return response


def top(request):    
    if not request.user.is_authenticated():
        if request.method == 'POST':
            if 'username' in request.POST:
                username = request.POST['username'].strip()
            if 'password' in request.POST:
                password = request.POST['password'].strip()
                
            user = authenticate(request, username=username, password=password)
        else:
            user = None
        if user is not None:
            login(request, user)
        else:
        # Return an 'invalid login' error message.

            return render(request, 'library/login.twig')
    
    return render(request, 'library/home.twig', {'categories': Category.objects.all()})

def logout_view(request):
    logout(request)
    return redirect('/')