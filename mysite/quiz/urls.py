from django.urls import path
from .views import QuizView
from . import views
urlpatterns = [
    path('<int:id>/', QuizView.as_view(), name='quiz_view'),
    path('', views.index, name='index'),
]