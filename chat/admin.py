from django.contrib import admin
from .models import Conversation, Message


class MessageInline(admin.TabularInline):
    """Inline display of messages within a conversation"""
    model = Message
    extra = 0
    fields = ['sender', 'content', 'message_type', 'timestamp', 'is_read']
    readonly_fields = ['timestamp']
    ordering = ['-timestamp']


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """Admin interface for Conversation model"""
    list_display = ['id', 'get_participants', 'product', 'created_at', 'updated_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['participants__username', 'product__name']
    readonly_fields = ['created_at', 'updated_at']
    filter_horizontal = ['participants']
    inlines = [MessageInline]
    
    def get_participants(self, obj):
        """Display participant usernames"""
        return ', '.join([user.username for user in obj.participants.all()])
    get_participants.short_description = 'Participants'
    
    def get_queryset(self, request):
        """Optimize queryset with prefetch_related"""
        qs = super().get_queryset(request)
        return qs.prefetch_related('participants', 'product')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Admin interface for Message model"""
    list_display = ['id', 'sender', 'conversation', 'message_type', 'timestamp', 'is_read']
    list_filter = ['message_type', 'is_read', 'timestamp']
    search_fields = ['content', 'sender__username']
    readonly_fields = ['timestamp']
    ordering = ['-timestamp']
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('sender', 'conversation')
