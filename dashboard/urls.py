from django.urls import path
from . import views

app_name = 'dashboard'

urlpatterns = [
    path('', views.home, name='home'),
    path('users/', views.user_list, name='user_list'),
    path('users/<int:pk>/toggle-lock/', views.user_toggle_lock, name='user_toggle_lock'),
    path('users/<int:pk>/set-role/', views.user_set_role, name='user_set_role'),
]