# view-like functions that implement an API
# the requirements are really simple so DRF is probably overkill

import datetime
from django.conf import settings
from django.db.models import Q, IntegerField
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth import authenticate, login, logout
from django.db.models.functions import Cast
from django.http import HttpResponse, FileResponse, JsonResponse
from django.shortcuts import render, redirect
from django.shortcuts import get_object_or_404
from django.utils.safestring import mark_safe
import django_tables2 as tables
from django_tables2 import RequestConfig
from django_tables2.utils import A
from django.views import View
from .models import Category
from .models import Entry
from .models import EntryMedia
from .models import Genre
from .models import Folder
from .models import FolderItem
from .models import Author
import os
import subprocess
import sys
from .utilx import error_log, makeimage
from django.core.serializers import serialize
from django.forms.models import model_to_dict
from rest_framework import serializers
from django.http import Http404
"""
        class Author {
            public $id;
            public $surname;
            public $given;
            public $bornyear;
            public $diedyear;
            public $country;
            public $realname; // Author
        }

        class BLEntry {
            public $title;
            public $pubyear;
            public $id;
            public $duration;
            public $fee;
            public $perfnotes;
            public $genre;
            public $ensemble;
            public $publisher;
            public $composer; // Author
            public $arranger; // Author
        }
"""


#class EntryMediaSerializer(serializers.ModelSerializer):
#    class Meta:
#        model = EntryMedia
#        fields = '__all__'

class AuthorSerializer(serializers.ModelSerializer):
    country = serializers.SlugRelatedField(
        read_only=True,
        slug_field='name'
    )
    full_name = serializers.SerializerMethodField()
    name = serializers.SerializerMethodField()

    def get_name(self, obj):

        if False and obj.realname:
            return "%s %s [%s]" % (obj.given, obj.surname, self.get_name(obj.realname))

        return "%s %s" % (obj.given, obj.surname)

    def get_full_name(self, obj):

        if obj.realname:
            return "%s %s [%s]" % (obj.given, obj.surname, self.get_full_name(obj.realname))

        if obj.bornyear or obj.diedyear:
            dates = " (%s-%s)" % (str(obj.bornyear) if obj.bornyear else "", str(obj.diedyear) if obj.diedyear else "")
        else:
            dates = ""

        return "%s %s%s%s" % (obj.given, obj.surname, dates, " - %s" % obj.country.name if obj.country else "")

    class Meta:
        model = Author
        fields = ['surname','given','bornyear','diedyear','country','realname','full_name','name']
        depth = 2

    def get_fields(self):
        fields = super().get_fields()
        fields['realname'] = AuthorSerializer(many=False)
        return fields

class EntrySerializer(serializers.ModelSerializer):
    genre = serializers.SlugRelatedField(
        read_only=True,
        slug_field='label'
    )
    ensemble = serializers.SlugRelatedField(
        read_only=True,
        slug_field='name'
    )
    publisher = serializers.SlugRelatedField(
        read_only=True,
        slug_field='name'
    )
    composer = AuthorSerializer()
    arranger = AuthorSerializer()
    class Meta:
        model = Entry
        fields = ['id','title','duration','fee','perfnotes','genre','ensemble','composer','arranger','publisher']
        depth = 2
        
class FolderEntrySerializer(serializers.ModelSerializer):
    genre = serializers.SlugRelatedField(
        read_only=True,
        slug_field='label'
    )
    ensemble = serializers.SlugRelatedField(
        read_only=True,
        slug_field='name'
    )
    
    class Meta:
        model = Entry
        fields = ['id','title', 'genre', 'ensemble']
        depth = 2

class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = ['id','label','issue_date']
        depth = 2

class FolderItemSerializer(serializers.ModelSerializer):
    entry = FolderEntrySerializer()
    class Meta:
        model = FolderItem
        fields = ['id', 'title', 'comment', 'position', 'entry']
        depth = 2

class StoreListView(View):
    def get(self, request, *args, **kwargs):
        entries = Entry.objects.filter(saleable=True).select_related('composer','arranger','ensemble','genre')
        eresponse = EntrySerializer(entries, many=True)
        message = {
            'type': 'BLCatalogue',
            'text': 'hello world',
            'entries': eresponse.data
        }
        return JsonResponse(message)

class StoreItemView(View):
    def get(self, request, *args, **kwargs):
#        index = kwargs['pk']

        try:
            entries = Entry.objects.filter(saleable=True, pk=kwargs['pk']).select_related('composer','arranger','ensemble','genre')
        except Entry.DoesNotExist:
            raise Http404("No such entry")

        if len(entries) == 0:
            raise Http404("No such entry")
        
        entry = entries[0]

        advert = entry.related_media.filter(asthumb=True).first()
        if advert:
            advertid = advert.id
        else:
            advertid = None

        eresponse = EntrySerializer(instance=entry).data
#        print("%s" % str(eresponse), file=sys.stderr)
        message = {
            'type': 'BLEntry',
            'text': 'entry!XXX',
            'entry': eresponse,
            'advert': advertid
        }

        # data = serialize("json", [message])
#        return HttpResponse(data, content_type="application/json")
        return JsonResponse(message)

class StoreMediaView(View):
    def get(self, request, *args, **kwargs):
#        index = kwargs['pk']
        try:
            entries = Entry.objects.filter(saleable=True, pk=kwargs['pk']).select_related(None)
        except Entry.DoesNotExist:
            raise Http404("No such entry")
        
        if len(entries) == 0:
            raise Http404("No such entry")

        media = entries[0].media
        if media:
            return makeimage(media.name, '', '')
        else:
            raise Http404("No media")

class FolderListView(View):
    def get(self, request, *args, **kwargs):
        entries = Folder.objects.all()
        eresponse = FolderSerializer(entries, many=True)
        message = {
            'type': 'FolderList',
            'text': 'hello world',
            'entries': eresponse.data
        }
        return JsonResponse(message)

class FolderView(View):
    def get(self, request, *args, **kwargs):
        try:
            entries = Folder.objects.filter(pk=kwargs['pk'])
        except Entry.DoesNotExist:
            raise Http404("No such entry")

        if len(entries) == 0:
            raise Http404("No such entry")
        
        entry = entries[0]
        eresponse = FolderItemSerializer(entry.slots, many=True)
        message = {
            'type': 'Folder',
            'text': 'hello world',
            'entries': eresponse.data
        }
        return JsonResponse(message)
