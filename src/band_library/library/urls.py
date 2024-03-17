from django.urls import path

from . import views, api

urlpatterns = [
    path('', views.index, name='index'),
    path('uploader/', views.upload_template, name='uploader'),
    path('entrydata/', views.index_json, name='entrydata'),
    path('entrylist/', views.entrylist, name='entrylist'),
    path('entry/<int:item>/', views.entry, name='entry'),
    path('incipit/<int:item>/', views.incipit, name='incipit'),
    path('chip/<int:item>/', views.chip, name='chip'),
    path('athumb/<int:item>/', views.athumb, name='athumb'),
    path('pagefile/<name>/', views.pagefile, name='pagefile'),
    path('folder/<str:folderid>/', views.folderlist, name='folderlist'),
    path('store/', api.StoreListView.as_view(), name='store-list'),
    path('store/<int:pk>/', api.StoreItemView.as_view(), name='store-item'),
    path('store/media/<int:pk>/', api.StoreMediaView.as_view(), name='store-media')
]