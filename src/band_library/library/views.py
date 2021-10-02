import datetime
from django.conf import settings
from django.db.models import Q, IntegerField
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import authenticate, login, logout
from django.db.models.functions import Cast
from django.http import HttpResponse, FileResponse
from django.shortcuts import render, redirect
from django.utils.safestring import mark_safe
import django_tables2 as tables
from django_tables2 import RequestConfig
from django_tables2.utils import A
from .models import Category
from .models import Entry
from .models import Genre
from .models import Folder
import os
import subprocess
import sys
from .utilx import error_log

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
        sequence = ('title', 'category', 'genre', 'callno', 'composer', 'arranger', 'instrument', 'media')

def is_number(zz):
    try:
        int(zz)
        return True
    except ValueError:
        return False

@login_required
def entry(request, item):
    limited = False
    limitcat = None
    if not request.user.is_staff and request.user.has_perm('library.march_only'):
        limited = True
        limitcat = 'M'

    if limited:
        entry = Entry.objects.filter(id__exact=item, category__code=limitcat).first()
        categories = None
    else:
        entry = Entry.objects.filter(id__exact=item).first()
        categories = Category.objects.all();

    return render(request, 'library/entry.twig', {'entry': entry, 'categories': categories, "can_edit": request.user.is_authenticated and request.user.is_staff, "limited": limited})


@login_required
def index(request):
    fff = Q()
    thewords = ""
    thecat = ""
    thegenre = ""
    entries = Entry.objects
    limited = False
    limitcat = None
    incomplete = False
    error_log("INDEX USER %s %s" % (str(request.user), str(request.user.user_permissions)))
    if not request.user.is_staff and request.user.has_perm('library.march_only'):
        limited = True
        limitcat = 'M'

    if limited:
        fff = Q(category__code__exact=limitcat)&Q(completeness__usable=True)
    else:
        if not 'incomplete' in request.GET:
            incomplete = False
            fff = fff & Q(completeness__usable=True)
        else:
            incomplete = True
        if 'words' in request.GET:
            www = request.GET['words'].strip()
            if www:
                wfilter = (Q(title__icontains=www) | Q(composer__given__icontains=www) | Q(composer__surname__icontains=www)| Q(arranger__given__icontains=www) | Q(arranger__surname__icontains=www))
                fff = fff & wfilter
                thewords = www

        if 'category' in request.GET:
            www = request.GET['category']
            if www and is_number(www):
                cfilter = (Q(category__exact=www))
                fff = fff & cfilter
                thecat = int(www)

        if 'genre' in request.GET:
            www = request.GET['genre']
            if www and is_number(www):
                cfilter = (Q(genre__exact=www))
                fff = fff & cfilter
                thegenre = int(www)

    if fff:
        table = EntryTable(entries.filter(fff))
    else:
        table = EntryTable(entries.all())
    if not request.user.is_staff:
        table.exclude = ('id', 'comments', 'callno', 'added', 'duration','incomplete')
    RequestConfig(request, paginate={'per_page': 50}).configure(table)
    return render(request, 'library/biglist.twig', {
        'entries': table,
        'categories': Category.objects.all(),
        'genres': Genre.objects.all(),
        'thewords': thewords,
        'thegenre': thegenre,
        'thecat': thecat,
        'limited': limited,
        'incomplete': incomplete
    })

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
    mfile = entry.media
    if mfile:
        fname = mfile.name
        res = '-r 16'
        return makeimage(fname, res, "chip-")
    else:
        return None

@permission_required('library.change_entry', login_url='/')
def pagefile(request, name):
    fullpath = os.path.join(mediadir, name)
    error_log("pagefile %s" % fullpath)

    ffc = open(fullpath, "rb")
    response = HttpResponse(ffc.read(), content_type="application/pdf")
    response['Cache-Control'] = "public"

    modtime = os.path.getmtime(fullpath)
    response['Last-Modified'] = datetime.datetime.utcfromtimestamp(modtime).strftime("%a, %d %b %y %H:%M:%S GMT")
    return response

def makeimage(fname, res, prefix):
    target = prefix + fname
    try:
#        error_log("open %s" % os.path.join(cachedir, target + ".jpg"))
        ffc = open(os.path.join(cachedir, target + ".jpg"), "rb")
    except:
        error_log("convert %s" % os.path.join(mediadir, fname))
        command = "pdftoppm -singlefile %s -jpeg \"%s\" \"%s\"" % (res, os.path.join(mediadir, fname), os.path.join(cachedir, target))
        error_log("command %s" % command)
        subprocess.call(command, shell=True)
        ffc = open(os.path.join(cachedir, target + ".jpg"), "rb")

    response = FileResponse(ffc, content_type="image/jpeg", charset='C')
    response['Cache-Control'] = "public"

    modtime = os.path.getmtime(os.path.join(cachedir, target + ".jpg"))
    response['Last-Modified'] = datetime.datetime.utcfromtimestamp(modtime).strftime("%a, %d %b %y %H:%M:%S GMT")
    return response


def top(request):
    if not request.user.is_authenticated:
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

    limited = False
    limitcat = None
    error_log("HOME USER %s %s" % (str(request.user), str(request.user.user_permissions.all())))
    if not request.user.is_staff and request.user.has_perm('library.march_only'):
        limited = True
        limitcat = 'M'
        categories = Category.objects.filter(code=limitcat)
    else:
        categories = Category.objects.all()

    genres = Genre.objects.all()
    folders = Folder.objects.all()

    return render(request, 'library/home.twig', {
        'categories': categories,
        'genres': genres,
        'folders': folders,
        'limited': limited
        })

def logout_view(request):
    logout(request)
    return redirect('/')

def folderlist(request, folderid):
    folder = Folder.objects.filter(pk__exact=folderid).first()
    return render(request, 'library/folderlist.twig', {'folder': folder})