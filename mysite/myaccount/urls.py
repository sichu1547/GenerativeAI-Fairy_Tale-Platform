from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # path('base/', views.base, name='base'),
    path('', views.index, name='index'),
    path('signup/', views.signup, name='signup'),  # 회원가입 URL
    path('login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('set-session/', views.set_session_data, name='set_session_data'),
    path('get-session/', views.get_session_data, name='get_session_data'), 
    path('password_reset/', views.password_reset_request, name='password_reset'),
    path('password_reset_done/', views.password_reset_done, name='password_reset_done'),
    path('reset/<uidb64>/<token>/', views.password_reset_confirm, name='password_reset_confirm'),
    path('reset/done/', views.password_reset_complete, name='password_reset_complete'),
    #path('select_account/', views.select_account, name='select_account'),
]
