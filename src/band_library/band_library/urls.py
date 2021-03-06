"""band_library URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import include, url
from django.contrib import admin
from django.http import HttpResponse

from library import views

admin.site.site_header = "Oakleigh Brass Library Admin"
admin.site.site_title = "Oakleigh Brass Library and Archive Admin"
admin.site.index_title = "Welcome to Oakleigh Brass Library and Archive"
# just to avoid disaster
admin.site.disable_action('delete_selected')

urlpatterns = [
    url(r'^$', views.top, name='home'),
    url(r'^logout$', views.logout_view, name='logout'),
    url(r'^library/', include('library.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^robots.txt$', lambda r: HttpResponse("User-agent: *\nDisallow: /", content_type="text/plain")) 
]
