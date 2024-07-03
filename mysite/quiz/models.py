from django.db import models

class ReaderStory(models.Model):
    title = models.CharField(max_length=200, default='non title')
    body = models.TextField()
    category = models.CharField(max_length=100, default='Uncategorized')
    class Meta:
        db_table = 'reader_story'
