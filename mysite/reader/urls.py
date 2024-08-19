from django.urls import path
from django.contrib import admin
from . import views
from django.contrib.auth import views as auth_views
app_name = 'reader'
urlpatterns = [
    path('', views.list, name='list'),
    path('search/', views.search, name='search'),
    path('story/<int:id>/', views.story_detail, name='story_detail'),
    path('story/<int:id>/quiz/', views.redirect_to_quiz, name='redirect_to_quiz'),
    path('generate_image/', views.generate_image_view, name='generate_image'),  # Add this line
    path('answer_question/<int:story_id>/', views.answer_question, name='answer_question'),  # AJAX 요청 처리용 URL
    path('rate_story/<int:id>/', views.rate_story, name='rate_story'),
    path('genstory/<int:story_id>/', views.genstory_detail, name='genstory_detail'),
    path('update_image_session/', views.update_image_session, name='update_image_session'),
    path('get_image_session/', views.get_image_session, name='get_image_session'),
]
