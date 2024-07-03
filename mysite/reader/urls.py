from django.urls import path
from django.contrib import admin
from . import views
from django.contrib.auth import views as auth_views
app_name = 'reader'
urlpatterns = [
    path('', views.list, name='list'),
    path('', views.index, name='index'),
    path('<int:id>', views.detail, name='detail'),
    path('search/', views.search, name='search'),
    path('story/<int:id>/', views.story_detail, name='story_detail'),    
    path('story/<int:id>/quiz/', views.redirect_to_quiz, name='redirect_to_quiz'),
]