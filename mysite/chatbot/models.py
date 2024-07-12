from django.db import models

# Create your models here.
class Chat(models.Model):
    id = models.AutoField(primary_key=True)
    user = models.TextField(default='unknown user')
    session = models.TextField(default='default session')
    datetime = models.DateTimeField(auto_now_add=True)
    user_question = models.TextField()
    chat_answer = models.TextField()
    sim1 = models.FloatField()
    sim2 = models.FloatField()
    sim3 = models.FloatField()