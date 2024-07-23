from django.contrib import admin
from django.urls import path
from django.shortcuts import redirect, render
import csv
from django.http import HttpResponse
from .models import *
import pandas as pd
import sqlite3
import mysql.connector

class StoryAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'category']
    list_display_links = ['id', 'title']
    ordering = ['id']
    list_filter = ['category']
    search_fields = ['body']

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
            
            df = pd.read_csv(csv_file, encoding='cp949')
            conn = mysql.connector.connect(
                host = settings.DB_HOST,
                user = settings.DB_USER,
                password = settings.DB_PASSWORD,
                database = settings.DB_NAME
            )   
            cursor = conn.cursor()
            cursor.execute('DELETE FROM reader_story')
            conn.commit()
            conn.close()                
            col = df.columns

            for _, row in df.iterrows():
                if len(row[col[1]]) < 50:
                    continue
 
                Story.objects.create(
                    title=row[col[0]],
                    body=row[col[1]],
                    category=row[col[2]],
                    keywords=row[col[3]].strip('[]').replace("'", "").split(','),
                    theme=row[col[4]]              
                )

            self.message_user(request, "CSV file uploaded successfully")
            return redirect(request.get_full_path())

        return render(request, self.upload_csv_template)

admin.site.register(Story, StoryAdmin)

class LogAdmin(admin.ModelAdmin):
    list_display = ['id', 'datetime', 'user', 'profile_name', 'story_title', 'question', 'answer']
    list_display_links = ['story_title', 'question', 'answer']
    list_filter = ['story_title']
admin.site.register(LogEntry, LogAdmin)