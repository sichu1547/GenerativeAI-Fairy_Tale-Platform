from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect, render
import csv
from django.http import HttpResponse
from .models import Story

class StoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'category']
    list_display_links = ['id', 'title']
    ordering = ['title']
    list_filter = ['tag', 'category']
    search_fields = ['body']
    #list_per_page = 3

    change_list_template = "admin/story_changelist.html"
    upload_csv_template = "admin/story_upload.html"
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('upload-csv/', self.upload_csv),
        ]
        return custom_urls + urls

    def upload_csv(self, request):
        if request.method == "POST" and 'csv_file' in request.FILES:
            csv_file = request.FILES["csv_file"]
            if not csv_file.name.endswith('.csv'):
                self.message_user(request, "This is not a csv file")
                return redirect(request.get_full_path())
            
            reader = csv.reader(csv_file.read().decode('utf-8').splitlines())
            next(reader)  # Skip the header
            for row in reader:
                if len(row[1]) < 50:
                    continue
                #print(row[0], len(row[1]))
                Story.objects.create(
                    title=row[0],
                    body=row[1],
                    category=row[2]
                )
            self.message_user(request, "CSV file uploaded successfully")
            return redirect(request.get_full_path())

        return render(request, self.upload_csv_template)

admin.site.register(Story, StoryAdmin)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)