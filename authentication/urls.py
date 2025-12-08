from django.urls import path
from . import views
from . import staff_views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('password-reset/', views.password_reset_view, name='password_reset'),
    # Settings URLs
    path('settings/', views.settings_view, name='settings'),
    path('settings/logout-all/', views.logout_all_sessions_view, name='logout_all_sessions'),
    # Profile URLs
    path('profile/', views.profile_view, name='profile'),
    path('profile/update-name/', views.update_name_view, name='update_name'),
    path('profile/update-email/', views.update_email_view, name='update_email'),
    path('profile/update-phone/', views.update_phone_view, name='update_phone'),
    path('profile/password/', views.change_password_view, name='change_password'),
    path('profile/picture/', views.upload_profile_picture_view, name='upload_profile_picture'),
    path('profile/business-permit/', views.upload_business_permit_view, name='upload_business_permit'),
    
    # API Endpoints
    path('api/farmer/<int:user_id>/', views.get_farmer_profile, name='get_farmer_profile'),
    
    # Staff Dashboard URLs
    path('staff/', staff_views.staff_dashboard, name='staff_dashboard'),
    # Farmer Verification
    path('staff/verifications/', staff_views.verification_list, name='staff_verification_list'),
    path('staff/verifications/<int:user_id>/', staff_views.verification_detail, name='staff_verification_detail'),
    path('staff/verifications/<int:user_id>/action/', staff_views.verification_action, name='staff_verification_action'),
    # Product Moderation
    path('staff/products/', staff_views.products_list, name='staff_products_list'),
    path('staff/products/<int:product_id>/action/', staff_views.product_action, name='staff_product_action'),
    path('staff/products/bulk-action/', staff_views.products_bulk_action, name='staff_products_bulk_action'),
    # User Management
    path('staff/users/', staff_views.users_list, name='staff_users_list'),
    path('staff/users/<int:user_id>/', staff_views.user_detail, name='staff_user_detail'),
    path('staff/users/<int:user_id>/action/', staff_views.user_action, name='staff_user_action'),
    # Conversation Management
    path('staff/conversations/', staff_views.conversations_list, name='staff_conversations_list'),
    path('staff/conversations/<int:conversation_id>/delete/', staff_views.conversation_delete, name='staff_conversation_delete'),
    path('staff/conversations/bulk-delete/', staff_views.conversations_bulk_delete, name='staff_conversations_bulk_delete'),
]

