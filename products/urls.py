from django.urls import path
from . import views

urlpatterns = [
    # Product listing and detail
    path('', views.product_list, name='product_list'),
    path('<int:pk>/', views.product_detail, name='product_detail'),
    
    # Product CRUD operations
    path('add/', views.product_create, name='product_create'),
    path('<int:pk>/edit/', views.product_edit, name='product_edit'),
    path('<int:pk>/delete/', views.product_delete, name='product_delete'),
    
    # Farmer's product management
    path('my-products/', views.my_products, name='my_products'),
    
    # Fair Price Calculator (Feature 6.2)
    path('calculator/', views.fair_price_view, name='fair_price_calculator'),
    path('calculator/delete/<int:calc_id>/', views.delete_saved_calculation, name='delete_saved_calculation'),
    path('api/calculate-fair-price/', views.calculate_fair_price_view, name='calculate_fair_price'),
]

