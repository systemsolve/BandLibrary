import datetime
from django.conf import settings
from django.db.models import Q
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import authenticate, login, logout
# from django.db.models.functions import Cast
from django.http import HttpResponse, FileResponse, JsonResponse
from django.shortcuts import render, redirect
from django.utils.safestring import mark_safe
import django_tables2 as tables
# from django_tables2 import RequestConfig
from django_tables2.utils import A
from .models import Category
from .models import Entry
from .models import Genre
from .models import Folder
from .models import AssetMedia
from .models import Ensemble
from .models import Asset
from . import forms as blforms

import os
# import subprocess
# import sys
import mimetypes
from .utilx import error_log, makeimage
from django.http import HttpResponseRedirect
from formtools.wizard.views import SessionWizardView


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
        template_name = 'django_tables2/bootstrap-responsive.html'
        attrs = {
            'class': 'paleblue table table-bordered table-striped table-hover',
            'id': 'entrytable',
            'style': 'width: 100%'
        }
        exclude = ('id', 'comments', 'media')
        fields = ('title', 'genre', 'composer', 'arranger')
        orderable = False
        empty_text = '-'
        # sequence = ('title', 'category', 'genre', 'callno', 'composer', 'arranger', 'instrument', 'media')


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
        categories = Category.objects.all()

    return render(request, 'library/entry.twig', {
        'devsys': settings.DEVSYS,
        'entry': entry,
        'categories': categories,
        'genres': Genre.objects.all(),
        "can_edit": request.user.is_authenticated and request.user.is_staff,
        "limited": limited})


def indexdata(request):
    fff = Q()
    thewords = ""
    thecat = ""
    thegenre = ""
    theensemble = ""

    limited = False
    limitcat = None
    incomplete = False
    error_log("INDEX USER %s %s" % (str(request.user), str(request.user.user_permissions)))
    if not request.user.is_staff and request.user.has_perm('library.march_only'):
        limited = True
        limitcat = 'M'

    if limited:
        fff = Q(category__code__exact=limitcat) & Q(completeness__usable=True)
    else:
        if not request.GET.get('incomplete', False):
            error_log("EXCLUDE INCOMPLETE")
            incomplete = ''
            fff = fff & Q(completeness__usable=True)
        else:
            error_log("INCLUDE INCOMPLETE")
            incomplete = '1'
        if 'words' in request.GET:
            www = request.GET['words'].strip()
            if www:
                wfilter = (
                    Q(title__icontains=www) |
                    Q(composer__given__icontains=www) |
                    Q(composer__surname__icontains=www)|
                    Q(arranger__given__icontains=www) |
                    Q(arranger__surname__icontains=www)
                )
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
                
        if 'ensemble' in request.GET:
            www = request.GET['ensemble']
            if www and is_number(www):
                cfilter = (Q(ensemble__exact=www))
                fff = fff & cfilter
                theensemble = int(www)
    # error_log("FILTER: %s" % str(fff))

    return fff, incomplete, thewords, thegenre, thecat, limited, theensemble


@login_required
def index(request):
    if request.method == 'POST':
        return redirect('/')
    entries = Entry.objects
    fff, incomplete, thewords, thegenre, thecat, limited, theensemble = indexdata(request)
    
    if fff:
        equery = entries.filter(fff)
    else:
        equery = entries.all()
        
    error_log("E QUERY: %s" % equery.query)
    
    table = EntryTable(equery)
    if not request.user.is_staff:
        table.exclude = ('id', 'comments', 'callno', 'added', 'duration', 'incomplete')
    # RequestConfig(request, paginate={'per_page': 50}).configure(table)
    return render(request, 'library/biglist.twig', {
        'devsys': settings.DEVSYS,
        'entries': table,
        'categories': Category.objects.all(),
        'genres': Genre.objects.all(),
        'ensembles': Ensemble.objects.all(),
        'thewords': thewords,
        'thegenre': thegenre,
        'theensemble': theensemble,
        'thecat': thecat,
        'limited': limited,
        'incomplete': incomplete
    })


@login_required
def index_json(request):
    entries = Entry.objects
    fff, incomplete, thewords, thegenre, thecat, limited, theensemble = indexdata(request)
    if fff:
        theentries = entries.filter(fff)
    else:
        theentries = entries.all()
        
    error_log("IJSON: %s" % theentries.query)

    if not request.user.is_staff:
        columns = (
            'id',
            'title',
            'genre__label',
            'ensemble__name',
            'composer__surname',
            'arranger__surname'
        )
        theentries = list(theentries.select_related('composer', 'arranger').values(*columns))
    else:
        columns = (
            'id',
            'title',
            'category__label',
            'callno',
            'genre__label',
            'ensemble__name',
            'composer__surname',
            'arranger__surname'
        )
        theentries = list(theentries.select_related('composer', 'arranger').values(*columns))
    # RequestConfig(request, paginate={'per_page': 50}).configure(table)
    return JsonResponse({'data': theentries, 'columns': columns})


@login_required
def entrylist(request):
    # fff is a Q object and won't be instantiated
    fff, incomplete, thewords, thegenre, thecat, limited, theensemble = indexdata(request)
    if not request.user.is_staff:
        columns = (('id', 'ID'), ('title', 'Title'),
                   ('genre__label', 'Genre'), ('ensemble__name', 'Ensemble'), ('composer__surname', 'Composer'), ('arranger__surname', 'Arranger'))
    else:
        columns = (('id', 'ID'),
                   ('title', 'Title'), ('category__label', 'Location'), ('callno', 'Label'), ('genre__label', 'Genre'), ('ensemble__name', 'Ensemble'),
                   ('composer__surname', 'Composer'), ('arranger__surname', 'Arranger'))

    return render(request, 'library/entrylist.twig', {
        'devsys': settings.DEVSYS,
        'columns': columns,
        'categories': Category.objects.all(),
        'genres': Genre.objects.all(),
        'ensembles': Ensemble.objects.all(),
        'thewords': thewords,
        'thegenre': thegenre,
        'theensemble': theensemble,
        'thecat': thecat,
        'limited': limited,
        'incomplete': incomplete
    })



@login_required
def assetlist(request):
    # fff is a Q object and won't be instantiated
    fff, incomplete, thewords, thegenre, thecat, limited = indexdata(request)
    if not request.user.is_staff:
        return redirect('/')
    else:
        columns = (('id', 'ID'),
                   ('title', 'Title'), ('category__label', 'Location'), ('callno', 'Label'), ('genre__label', 'Genre'),
                   ('composer__surname', 'Composer'), ('arranger__surname', 'Arranger'))

    return render(request, 'library/entrylist.twig', {
        'devsys': settings.DEVSYS,
        'columns': columns,
        'categories': Category.objects.all(),
        'genres': Genre.objects.all(),
        'thewords': thewords,
        'thegenre': thegenre,
        'thecat': thecat,
        'limited': limited,
        'incomplete': incomplete
    })


@login_required
def assets_json(request):
    entries = Asset.objects
    fff, incomplete, thewords, thegenre, thecat, limited = indexdata(request)
    if fff:
        theentries = entries.filter(fff)
    else:
        theentries = entries.all()

    if not request.user.is_staff:
        return JsonResponse({'data': None, 'columns': None})
    else:
        columns = (
            'id',
            'title',
            'category__label',
            'callno',
            'genre__label',
            'composer__surname',
            'arranger__surname'
        )
        theentries = list(theentries.select_related('composer', 'arranger').values(*columns))
    # RequestConfig(request, paginate={'per_page': 50}).configure(table)
    return JsonResponse({'data': theentries, 'columns': columns})


# basedir = '/Users/david/src/BandLibrary'
# mediadir = os.path.join(basedir, 'media')
# cachedir = os.path.join(basedir, 'mediacache')
mediadir = settings.BL_MEDIADIR


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


@login_required
def athumb(request, item, resv=64):
    entry = AssetMedia.objects.filter(pk__exact=item).first()
    if entry and entry.mfile:
        fname = entry.mfile.name
        fullpath = os.path.join(mediadir, fname)
        ffc = open(fullpath, "rb")
        response = FileResponse(ffc, content_type="image/jpeg", charset='C')
        response['Cache-Control'] = "public"

        modtime = os.path.getmtime(fullpath)
        response['Last-Modified'] = datetime.datetime.utcfromtimestamp(modtime).strftime("%a, %d %b %y %H:%M:%S GMT")
        return response
#        res = '-r %d' % resv if resv else ''
#        return makeimage(fname, res, "athumb-")
    else:
        return None


@permission_required('library.change_entry', login_url='/')
def pagefile(request, name):
    fullpath = os.path.join(mediadir, name)
    error_log("pagefile %s" % fullpath)

    ffc = open(fullpath, "rb")
    content_type = mimetypes.guess_type(fullpath)
    response = HttpResponse(ffc.read(), content_type=content_type[0])
    response['Cache-Control'] = "public"

    modtime = os.path.getmtime(fullpath)
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
    if request.method == 'POST':
        return redirect('/')

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
    ensembles = Ensemble.objects.all()

    return render(request, 'library/home.twig', {
        'devsys': settings.DEVSYS,
        'categories': categories,
        'genres': genres,
        'folders': folders,
        'ensembles': ensembles,
        'limited': limited
    })


def logout_view(request):
    logout(request)
    return redirect('/')


def folderlist(request, folderid):
    # TODO: speed up query - use prefetch_related to pull "slots" and "slots__entry"
    folder = Folder.objects.filter(pk__exact=folderid).first()
    return render(request, 'library/folderlist.twig', {'devsys': settings.DEVSYS, 'folder': folder})


@login_required
def upload_template(request):
    import csv
    # ID (optional), Category (code), Title, Label, Ensemble, Duration, Composer, Arranger, Force update
    field_names = [
        'Optional ID',
        "Category Code",
        "Title",
        "Label",
        "Ensemble",
        "Duration (0:0 if none)",
        "Composer",
        "Arranger",
        "Force update (Y)"
    ]

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename=libtemplate.csv'
    writer = csv.writer(response)
    writer.writerow(field_names)
    return response


CHECKINFORMS = [
    ("start", blforms.CheckinForm1),
    ("finish", blforms.MaintForm)
]


class CheckinWizard(SessionWizardView):
    template_name = "library/checkin.twig"
    form_list = CHECKINFORMS

    def done(self, form_list, **kwargs):
        # do_something_with_the_form_data(form_list)
        formdata = self.get_all_cleaned_data()
        error_log("DONE: %s" % str(formdata))

        instrument = formdata.get('instrument')

        instrument.asset_status_id = formdata['purpose']
        instrument.location = "%s====\n%s\nRETURNED\n%s" % (
            instrument.location,
            datetime.datetime.now(),
            formdata['notes']
            )

        instrument.save()

        return redirect('oneasset', item=instrument.id)


CHECKOUTFORMS = [
    ("start", blforms.CheckoutForm1),
    ("instrument", blforms.CheckoutForm2),
    ("usage", blforms.CheckoutForm3),
    ("final", blforms.BorrowForm)
]


class CheckoutWizard(SessionWizardView):
    template_name = "library/checkout.twig"
    form_list = CHECKOUTFORMS

    def get_form(self, step=None, data=None, files=None):
        form = super().get_form(step, data, files)

        # determine the step if not given
        if step is None:
            step = self.steps.current

        error_log("XXX handle step %s" % step)
        if step == 'instrument':
            xxx = self.get_cleaned_data_for_step("start")
            error_log("XXX %s data %s" % (str(step), str(xxx)))
            form = blforms.CheckoutForm2(choice=xxx['instrument_type'], data=data)
            form.typename = str(xxx['instrument_type'])
        if step == 'usage':
            xxx = self.get_cleaned_data_for_step("instrument")
            yyy = self.get_cleaned_data_for_step("start")
            error_log("XXX %s data %s AND %s" % (str(step), str(yyy), str(xxx)))
            if False and yyy['purpose'] == 'MAINT':
                form = blforms.MaintForm(data=data)
            else:
                form = blforms.CheckoutForm3(data=data)
            form.typename = str(xxx['instrument'])

        return form

    def get_context_data(self, form, **kwargs):
        context = super().get_context_data(form=form, **kwargs)
        if self.steps.current in ['instrument', 'usage']:
            context.update({'typename': form.typename})
        return context

    def done(self, form_list, **kwargs):
        # do_something_with_the_form_data(form_list)
        formdata = self.get_all_cleaned_data()
        error_log("DONE: %s" % str(formdata))

        instrument = formdata.get('instrument')

        instrument.asset_status_id = formdata['purpose']
        instrument.location = "%s===\n%s\n%s|%s|%s\n%s" % (
            instrument.location,
            datetime.datetime.now(),
            formdata['name'],
            formdata['phone'],
            formdata['email'],
            formdata['address'])

        instrument.save()

        return redirect('oneasset', item=instrument.id)


@login_required
def oneasset(request, item):
    limited = False
    limitcat = None

    entry = Asset.objects.filter(id__exact=item).select_related('asset_status').first()

    return render(request, 'library/oneasset.twig', {
        'devsys': settings.DEVSYS,
        'asset': entry,
        "can_edit": request.user.is_authenticated and request.user.is_staff,
        "limited": limited})