from django.urls import path
from django.contrib import admin
from . import views
from django.contrib.auth import views as auth_views

app_name = 'generator'
urlpatterns = [
    path('', views.index, name='index'),
    path('create_story', views.create_story, name='create_story'),
]