from django.db.models import Subquery

from .models import Conversation, Message


def unread_messages_count(request):
    """
    Context processor to add unread message count to all templates
    """
    if request.user.is_authenticated:
        conversations = Conversation.objects.filter(
            participants=request.user
        ).exclude(
            deleted_by=request.user
        ).distinct().values('pk')

        total_unread = Message.objects.filter(
            conversation_id__in=Subquery(conversations),
            is_read=False
        ).exclude(
            sender=request.user
        ).count()

        return {
            'unread_messages_count': total_unread
        }
    
    return {
        'unread_messages_count': 0
    }

