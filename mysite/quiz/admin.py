from django.contrib import admin
from .models import ReaderStory

class ReaderStoryAdmin(admin.ModelAdmin):
    list_display = ('category', 'title', 'body')

admin.site.register(ReaderStory, ReaderStoryAdmin)