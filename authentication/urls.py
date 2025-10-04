from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('register/farmer/', views.register_view, {'user_type': 'farmer'}, name='register_farmer'),
    path('register/buyer/', views.register_view, {'user_type': 'buyer'}, name='register_buyer'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('password-reset/', views.password_reset_view, name='password_reset'),
]

