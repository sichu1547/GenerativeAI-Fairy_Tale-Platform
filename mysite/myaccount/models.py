from django.db import models
from django.contrib.auth.models import User

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
    name = models.CharField(max_length=255)
    avatar = models.ImageField(upload_to='avatars/', default='avatars/ru8.jpg')

    def __str__(self):
        return self.name