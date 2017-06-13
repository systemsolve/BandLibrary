from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.index, name='index'),
    url(r'^entry/(?P<item>[0-9]+)/$', views.entry, name='entry'),
    url(r'^incipit/(?P<item>[0-9]+)/$', views.incipit, name='incipit'),
    url(r'^chip/(?P<item>[0-9]+)/$', views.chip, name='chip'),
    
]