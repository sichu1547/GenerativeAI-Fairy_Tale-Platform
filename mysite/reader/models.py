from django.db import models
from django.urls import reverse

# Create your models here.
class Story(models.Model):
    title = models.CharField(max_length=250)
    body = models.TextField()
    # tag = models.ManyToManyField('Tag', blank=True)
    category = models.CharField(max_length=100, default='Uncategorized')
    keywords = models.CharField(max_length=1000, blank=True, default=None, null=True)
    theme = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse("reader:detail", kwargs={"id": self.id})
    
class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.name
    
class LogEntry(models.Model):
    datetime = models.DateTimeField(auto_now_add=True)
    story_title = models.CharField(max_length=200)  # 동화 제목 필드 추가
    question = models.TextField()
    answer = models.TextField()
 
    def __str__(self):
        return f"Story: {self.story_title}, Question: {self.question[:]}, Answer: {self.answer[:50]}"