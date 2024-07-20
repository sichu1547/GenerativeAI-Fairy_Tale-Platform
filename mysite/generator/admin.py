from django.contrib import admin
from django.urls import path
from .models import *


class GenStoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'datetime', 'title']
    list_display_links = ['id', 'title']
    ordering = ['id']
    search_fields = ['body']
    #list_per_page = 3

admin.site.register(GenStory, GenStoryAdmin)