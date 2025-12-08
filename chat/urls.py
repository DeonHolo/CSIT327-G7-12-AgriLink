from django.urls import path
from . import views

urlpatterns = [
    # Conversation list and detail
    path('', views.conversation_list, name='conversation_list'),
    path('<int:pk>/', views.conversation_detail, name='conversation_detail'),
    path('<int:pk>/delete/', views.delete_conversation, name='delete_conversation'),
    
    # Message actions
    path('<int:pk>/send/', views.message_send, name='message_send'),
    path('<int:pk>/mark-read/', views.mark_messages_read, name='mark_messages_read'),
    path('<int:pk>/messages/new/<str:after_timestamp>/', views.get_new_messages, name='get_new_messages'),
    
    # Typing indicators
    path('<int:pk>/typing/', views.send_typing, name='send_typing'),
    path('<int:pk>/typing/status/', views.get_typing_status, name='get_typing_status'),
    
    # Start conversation from product
    path('start/<int:product_pk>/', views.start_conversation, name='start_conversation'),
    
    # Deal management
    path('<int:pk>/farmer-products/', views.get_farmer_products, name='get_farmer_products'),
    path('<int:pk>/create-offer/', views.create_offer, name='create_offer'),
    path('<int:pk>/deals/', views.get_conversation_deals, name='get_conversation_deals'),
    path('deal/<int:deal_id>/', views.get_deal, name='get_deal'),
    path('deal/<int:deal_id>/accept/', views.accept_deal, name='accept_deal'),
    path('deal/<int:deal_id>/decline/', views.decline_deal, name='decline_deal'),
    path('deal/<int:deal_id>/cancel/', views.cancel_deal, name='cancel_deal'),
    path('deal/<int:deal_id>/complete/', views.complete_deal, name='complete_deal'),
    path('deal/<int:deal_id>/review/', views.submit_review, name='submit_review'),
]

