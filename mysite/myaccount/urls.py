from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('signup/', views.signup, name='signup'),  # 회원가입 URL
    path('login/', views.CustomLoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('set-session/', views.set_session_data, name='set_session_data'),
    path('get-session/', views.get_session_data, name='get_session_data'), 
    path('password_reset/', views.password_reset_request, name='password_reset'),
    path('password_reset_done/', views.password_reset_done, name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('reset/done/', views.password_reset_complete, name='password_reset_complete'),
    path('select_account/', views.select_account, name='select_account'),
    path('profile/', views.profile, name='profile'),
    path('profile/<int:pk>/', views.profile_detail, name='profile_detail'),
    path('choose_profile/<int:profile_id>/', views.choose_profile, name='choose_profile'),
    path('reading-history/<int:profile_id>/', views.reading_history, name='reading_history'),
    path('attendance_check/', views.attendance_check, name='attendance_check'),
    path('reset_show_attendance_modal/', views.reset_show_attendance_modal, name='reset_show_attendance_modal'),
    path('profile/<int:pk>/edit/', views.edit_profile, name='edit_profile'),
    path('profile/<int:pk>/delete/', views.profile_delete, name='profile_delete'),
    path('privacy_policy/', views.privacy_policy_view, name='privacy_policy'),
    path('terms/', views.terms, name='terms'),
    path('check_username/', views.check_username, name='check_username'),
]
