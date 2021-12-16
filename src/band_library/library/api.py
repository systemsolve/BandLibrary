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
import os
import subprocess
import sys
from .utilx import error_log, makeimage
from django.core.serializers import serialize
from django.forms.models import model_to_dict
from rest_framework import serializers


class EntryMediaSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntryMedia
        fields = '__all__'
        
class EntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Entry
        fields = '__all__'

class StoreListView(View):
    def get(self, request, *args, **kwargs):
        entries = Entry.objects.filter(saleable=True).values('id', 'title','composer__surname','arranger__surname','ensemble__name', 'duration', 'fee')
        message = {
            'type': 'greeting',
            'text': 'hello world',
            'entries': list(entries)
        }
        return JsonResponse(message)
    
class StoreItemView(View):
    def get(self, request, *args, **kwargs):
#        index = kwargs['pk']
        entry = get_object_or_404(Entry, pk=kwargs['pk'], saleable=True)
        advert = entry.related_media.filter(asthumb=True).first()
        if advert:
            advertid = advert.id
        else:
            advertid = None
        
        eresponse = EntrySerializer(instance=entry).data
#        print("%s" % str(eresponse), file=sys.stderr)
        message = {
            'type': 'detail',
            'text': 'entry!',
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
