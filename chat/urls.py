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
    
    # Start conversation from product
    path('start/<int:product_pk>/', views.start_conversation, name='start_conversation'),
]

