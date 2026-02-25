from django import views
from django.urls import path
from .views import login_view, signup_view, logout_view, superadmin_dashboard, admin_dashboard, profile_view
from . import views

urlpatterns = [
    path('', login_view, name='login'),
    path('signup/', signup_view, name='signup'),
    path('logout/', logout_view, name='logout'),
    path('superadmin/', superadmin_dashboard, name='superadmin_dashboard'),
    path('admin-panel/', admin_dashboard, name='admin_dashboard'),
    path('profile/', profile_view, name='profile'),
    path('user/tokens/', views.user_token_page, name='user_token_page'),
    path('user/logout/', views.user_logout_view, name='user_logout'),
    
]