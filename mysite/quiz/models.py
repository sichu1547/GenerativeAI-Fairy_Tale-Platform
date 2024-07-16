from django.db import models

class History(models.Model):
    story_id = models.IntegerField()
    question = models.TextField()
    answer = models.TextField()
    def __str__(self):
        return f"Story ID: {self.story_id}, Question: {self.question}, Answer: {self.answer}"