from django.db import models
from django.contrib.auth.models import User
from myaccount.models import Profile
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

class GenStory(models.Model):
    title = models.CharField(max_length=250)
    body = models.TextField()
    category = models.CharField(max_length=100, default='Generative')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE)
    starpoint = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], blank=True, null=True, default=0)
    starcount = models.IntegerField(default=0)
    starsum = models.IntegerField(default=0)
    datetime = models.DateTimeField(default=timezone.now)
    thumbnail = models.ImageField(upload_to="gen_thumbnails/", null=True)