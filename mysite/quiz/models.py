from django.db import models

class ReaderStory(models.Model):
    title = models.CharField(max_length=200, default='non title')
    body = models.TextField()

    class Meta:
        #app_label = 'quiz'
        db_table = 'reader_story'
        #db_table = 'django_session'
