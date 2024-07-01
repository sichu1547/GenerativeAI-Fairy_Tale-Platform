from django.urls import path
from .views import QuizView

app_name = 'quiz'
urlpatterns = [
    path('<int:id>/', QuizView.as_view(), name='quiz_view'),
]
