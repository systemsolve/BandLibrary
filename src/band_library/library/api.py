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
        fields = ['surname','given','bornyear','diedyear','country','realname','full_name']
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

class StoreListView(View):
    def get(self, request, *args, **kwargs):
        entries = Entry.objects.filter(saleable=True).values('id', 'title','composer__surname','arranger__surname','ensemble__name', 'duration', 'fee')
        message = {
            'type': 'BLCatalogue',
            'text': 'hello world',
            'entries': list(entries)
        }
        return JsonResponse(message)
    
class StoreItemView(View):
    def get(self, request, *args, **kwargs):
#        index = kwargs['pk']

        try:
            entries = Entry.objects.filter(saleable=True, pk=kwargs['pk']).select_related('composer','arranger','ensemble')
        except Entry.DoesNotExist:
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
        entry = get_object_or_404(EntryMedia, pk=kwargs['pk'])
        
        return makeimage(entry.mfile.name, '', '')
        
#        eresponse = EntryMediaSerializer(instance=entry).data
##        print("%s" % str(eresponse), file=sys.stderr)
#        message = {
#            'type': 'detail',
#            'text': 'media!',
#            'entry': eresponse,
#        }
#        
#        # data = serialize("json", [message])
##        return HttpResponse(data, content_type="application/json")
#        return JsonResponse(message)
