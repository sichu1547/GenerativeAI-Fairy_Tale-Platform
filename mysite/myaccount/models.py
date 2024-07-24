from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class UserSessionData(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    session_data = models.JSONField(default=dict)  # 세션 데이터를 JSON 형식으로 저장

    def __str__(self):
        return f"Session data for user {self.user.username}"

class PasswordResetRequest(models.Model):
    email = models.EmailField()
    requested_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.email
    
class Profile(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='profiles')
    profile_id = models.PositiveIntegerField(editable=False)
    name = models.CharField(max_length=255)
    avatar = models.ImageField(upload_to='avatars/', default='avatars/default.png')
    full_profile_id = models.CharField(max_length=255, editable=False, unique=True, default=1)
    date = models.DateField(default=timezone.now)
    attendance_dates = models.JSONField(default=list)
    
    class Meta:
        unique_together = ('user', 'profile_id')

    def save(self, *args, **kwargs):
        if not self.pk: 
            max_profile_id = Profile.objects.filter(user=self.user).aggregate(models.Max('profile_id'))['profile_id__max']
            self.profile_id = (max_profile_id or 0) + 1
        self.full_profile_id = f"{self.user.id}-{self.profile_id}"
        super(Profile, self).save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - {self.name}"
    
class ReadingHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reading_histories')
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='reading_histories')
    story_title = models.CharField(max_length=200, default='')
    story_id = models.IntegerField(default=4962)
    read_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.profile.name} - {self.story_title}"  