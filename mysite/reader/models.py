from django.db import models
from django.urls import reverse

# Create your models here.
class Story(models.Model):
    title = models.CharField(max_length=250)
    body = models.TextField()
    tag = models.ManyToManyField('Tag', blank=True)
    category = models.CharField(max_length=100, default='Uncategorized')

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse("reader:detail", kwargs={"id": self.id})
    
class Tag(models.Model):
    name = models.CharField(max_length=50, unique=True)
    
    def __str__(self):
        return self.name