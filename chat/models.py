from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Conversation(models.Model):
    """
    Conversation between users (typically farmer and buyer)
    Implements FR-14, FR-15 (Chat module requirements)
    """
    participants = models.ManyToManyField(
        User,
        related_name='conversations',
        help_text='Users participating in this conversation'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='conversations',
        help_text='Product this conversation is about (optional)'
    )
    deleted_by = models.ManyToManyField(
        User,
        related_name='deleted_conversations',
        blank=True,
        help_text='Users who have deleted this conversation on their end'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'conversations'
        verbose_name = 'Conversation'
        verbose_name_plural = 'Conversations'
        ordering = ['-updated_at']
        indexes = [
            models.Index(fields=['-updated_at']),
        ]
    
    def __str__(self):
        participant_names = ', '.join([user.username for user in self.participants.all()[:2]])
        return f"Conversation: {participant_names}"
    
    def get_other_participant(self, user):
        """Get the other participant in the conversation"""
        return self.participants.exclude(id=user.id).first()
    
    def get_last_message(self):
        """Get the most recent message in this conversation"""
        return self.messages.order_by('-timestamp').first()
    
    def get_unread_count(self, user):
        """Get count of unread messages for a specific user"""
        return self.messages.filter(is_read=False).exclude(sender=user).count()
    
    def is_deleted_by(self, user):
        """Check if this conversation is deleted by a specific user"""
        return self.deleted_by.filter(id=user.id).exists()
    
    def delete_for_user(self, user):
        """Mark conversation as deleted for a specific user"""
        self.deleted_by.add(user)
    
    def restore_for_user(self, user):
        """Restore conversation for a specific user (undelete)"""
        self.deleted_by.remove(user)


class Message(models.Model):
    """
    Individual message within a conversation
    Implements FR-15, FR-16 (Message history with timestamp, quick actions)
    """
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    content = models.TextField(help_text='Message content')
    timestamp = models.DateTimeField(default=timezone.now)
    is_read = models.BooleanField(
        default=False,
        help_text='Whether the message has been read by recipient'
    )
    
    # Quick action types (FR-16: Order Now, Request Price)
    MESSAGE_TYPES = (
        ('text', 'Text Message'),
        ('order_request', 'Order Request'),
        ('price_request', 'Price Request'),
    )
    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPES,
        default='text'
    )
    
    class Meta:
        db_table = 'messages'
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        ordering = ['timestamp']
        indexes = [
            models.Index(fields=['conversation', 'timestamp']),
            models.Index(fields=['is_read']),
        ]
    
    def __str__(self):
        return f"{self.sender.username}: {self.content[:50]}"
    
    def mark_as_read(self):
        """Mark this message as read"""
        if not self.is_read:
            self.is_read = True
            self.save(update_fields=['is_read'])
