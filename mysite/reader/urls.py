from django.urls import path
from django.contrib import admin
from . import views
from django.contrib.auth import views as auth_views
app_name = 'reader'
urlpatterns = [
    path('', views.list, name='list'),
    path('<int:id>', views.detail, name='detail'),
]