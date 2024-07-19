from django.db import models
from django.urls import reverse
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.contrib.auth.models import User

class Story(models.Model):
    title = models.CharField(max_length=250)
    body = models.TextField()
    category = models.CharField(max_length=100, default='Uncategorized')
    keywords = models.CharField(max_length=1000, blank=True, default=None, null=True)
    theme = models.CharField(max_length=100, blank=True, null=True)
    starpoint = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], blank=True, null=True, default=0)
    starcount = models.IntegerField(default=0)
    starsum = models.IntegerField(default=0)
    image = models.ImageField(upload_to='images/', blank=True, null=True)
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse("reader:detail", kwargs={"id": self.id})
    

class LogEntry(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='admin_log_entries', default=1)
    profile_id = models.IntegerField(default=4962)
    profile_name = models.CharField(max_length=255, default='')
    datetime = models.DateTimeField(auto_now_add=True)
    story_title = models.CharField(max_length=200)
    question = models.TextField()
    answer = models.TextField()


    def __str__(self):
        return f"Story: {self.story_title}, Question: {self.question[:]}, Answer: {self.answer[:50]}"