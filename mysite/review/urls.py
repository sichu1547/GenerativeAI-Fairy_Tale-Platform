from django.urls import path
from .views import ReviewView
from django.views.generic import TemplateView
from .views import ReviewListView, ReviewDeleteView
app_name = 'review'

urlpatterns = [
    path('write/<int:story_id>/', ReviewView.as_view(), name='write_review'),
    path('success/', TemplateView.as_view(template_name='review/success.html'), name='review_success'),
    path('list/<int:review_id>/', ReviewListView.as_view(), name='review_list'),
    path('delete/<int:pk>/', ReviewDeleteView.as_view(), name='review_delete'),
]
