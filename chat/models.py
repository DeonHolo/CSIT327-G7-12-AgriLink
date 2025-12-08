from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from decimal import Decimal

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


class Deal(models.Model):
    """
    Deal/Transaction between farmer and buyer within a conversation.
    Represents an offer made by the farmer for specific products.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('declined', 'Declined'),
    ]
    
    conversation = models.ForeignKey(
        Conversation,
        on_delete=models.CASCADE,
        related_name='deals',
        help_text='Conversation this deal belongs to'
    )
    product = models.ForeignKey(
        'products.Product',
        on_delete=models.CASCADE,
        related_name='deals',
        help_text='Product being sold in this deal'
    )
    farmer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='deals_as_farmer',
        help_text='Farmer/seller creating this deal'
    )
    buyer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='deals_as_buyer',
        help_text='Buyer receiving this deal offer'
    )
    quantity = models.PositiveIntegerField(
        help_text='Quantity of product in this deal'
    )
    unit_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Price per unit at time of deal creation'
    )
    total_price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Total price (can be overridden for discounts)'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        help_text='Current status of the deal'
    )
    cancelled_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cancelled_deals',
        help_text='User who cancelled this deal (if cancelled)'
    )
    cancellation_reason = models.TextField(
        blank=True,
        help_text='Reason for cancellation (optional)'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the buyer accepted the deal'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the buyer confirmed receipt'
    )
    
    class Meta:
        db_table = 'deals'
        verbose_name = 'Deal'
        verbose_name_plural = 'Deals'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status']),
            models.Index(fields=['conversation']),
            models.Index(fields=['farmer']),
            models.Index(fields=['buyer']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"Deal #{self.pk}: {self.quantity} {self.product.unit} of {self.product.name} - {self.get_status_display()}"
    
    def can_be_accepted(self):
        """Check if this deal can still be accepted"""
        return self.status == 'pending'
    
    def can_be_cancelled(self, user):
        """Check if this deal can be cancelled by the given user"""
        if self.status == 'pending':
            # Only farmer can cancel pending offers
            return user == self.farmer
        elif self.status == 'confirmed':
            # Either party can cancel confirmed orders
            return user in [self.farmer, self.buyer]
        return False
    
    def can_be_completed(self, user):
        """Check if this deal can be marked as completed by the given user"""
        return self.status == 'confirmed' and user == self.buyer
    
    @property
    def is_reviewed(self):
        """Check if this deal has been reviewed"""
        return hasattr(self, 'review')


class Review(models.Model):
    """
    Dual-rating review for a completed deal.
    Contains separate ratings for the seller and the product.
    """
    deal = models.OneToOneField(
        Deal,
        on_delete=models.CASCADE,
        related_name='review',
        help_text='The completed deal this review is for'
    )
    reviewer = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='reviews_given',
        help_text='The buyer who wrote this review'
    )
    # Seller rating
    seller_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Rating for the seller (1-5 stars)'
    )
    seller_comment = models.TextField(
        blank=True,
        help_text='Comment about the seller service'
    )
    # Product rating
    product_rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text='Rating for the product (1-5 stars)'
    )
    product_comment = models.TextField(
        blank=True,
        help_text='Comment about the product quality'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'reviews'
        verbose_name = 'Review'
        verbose_name_plural = 'Reviews'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return f"Review for Deal #{self.deal.pk} by {self.reviewer.username}"
    
    def save(self, *args, **kwargs):
        """Override save to update aggregate ratings"""
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new:
            # Update farmer's average rating
            self._update_farmer_rating()
            # Update product's average rating
            self._update_product_rating()
    
    def _update_farmer_rating(self):
        """Update the farmer's aggregate rating"""
        farmer = self.deal.farmer
        from django.db.models import Avg, Count
        
        # Get all reviews for this farmer's deals
        reviews = Review.objects.filter(deal__farmer=farmer)
        aggregates = reviews.aggregate(
            avg_rating=Avg('seller_rating'),
            count=Count('id')
        )
        
        farmer.average_farmer_rating = aggregates['avg_rating'] or 0
        farmer.farmer_rating_count = aggregates['count']
        farmer.save(update_fields=['average_farmer_rating', 'farmer_rating_count'])
    
    def _update_product_rating(self):
        """Update the product's aggregate rating"""
        product = self.deal.product
        from django.db.models import Avg, Count
        
        # Get all reviews for this product's deals
        reviews = Review.objects.filter(deal__product=product)
        aggregates = reviews.aggregate(
            avg_rating=Avg('product_rating'),
            count=Count('id')
        )
        
        product.average_rating = aggregates['avg_rating'] or 0
        product.rating_count = aggregates['count']
        product.save(update_fields=['average_rating', 'rating_count'])
