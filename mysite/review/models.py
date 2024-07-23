from django.db import models
from django.contrib.auth.models import User
from reader.models import Story
from django.utils import timezone
from myaccount.models import Profile

class Review(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # content = models.TextField()
    story_title = models.CharField(max_length=200, default='')
    title = models.CharField(max_length=200, default='')
    created_at = models.DateTimeField(default=timezone.now)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, default=2)
    # main_character = models.TextField(default='')  # 주인공에 대한 내용
    # ending = models.TextField(default='')          # 결말에 대한 내용
    # author_thoughts = models.TextField(default='') # 필자의 생각
    painting = models.ImageField(upload_to='review_paintings/', null=True, blank=True)

    def __str__(self):
        return self.title
