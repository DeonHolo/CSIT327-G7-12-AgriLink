from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone


class User(AbstractUser):
    """
    Custom User model extending Django's AbstractUser
    """
    USER_TYPES = (
        ('farmer', 'Farmer'),
        ('buyer', 'Buyer'),
        ('both', 'Both'),
    )
    
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    user_type = models.CharField(
        max_length=10, 
        choices=USER_TYPES, 
        default='buyer',
        help_text='User role in the platform'
    )
    profile_picture = models.ImageField(
        upload_to='profile_pictures/',
        blank=True,
        null=True,
        help_text='User profile picture'
    )
    BUSINESS_PERMIT_STATUSES = (
        ('none', 'Not submitted'),
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )
    business_permit = models.FileField(
        upload_to='business_permits/',
        blank=True,
        null=True,
        help_text='Business permit document for farmer verification'
    )
    business_permit_status = models.CharField(
        max_length=10,
        choices=BUSINESS_PERMIT_STATUSES,
        default='none',
        help_text='Verification status for farmer role request'
    )
    business_permit_notes = models.TextField(
        blank=True,
        help_text='Admin notes for verification (optional)'
    )
    business_permit_updated_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text='Last time permit status was updated'
    )
    average_farmer_rating = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0,
        help_text='Average rating from buyers'
    )
    farmer_rating_count = models.PositiveIntegerField(
        default=0,
        help_text='Number of ratings received as a farmer'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)
    
    # Notification preferences
    notify_chat = models.BooleanField(
        default=True,
        help_text='Receive notifications for new chat messages'
    )
    notify_permit_decision = models.BooleanField(
        default=True,
        help_text='Receive notifications for business permit decisions'
    )
    
    class Meta:
        db_table = 'users'
        verbose_name = 'User'
        verbose_name_plural = 'Users'
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"
    
    def is_farmer(self):
        return self.user_type in ['farmer', 'both']
    
    def is_buyer(self):
        return self.user_type in ['buyer', 'both']
    
    def has_pending_farmer_request(self):
        """Check if user has a pending farmer verification request."""
        return self.business_permit_status == 'pending'
    
    def approve_farmer_request(self, approved_by=None, notes=''):
        """
        Approve farmer verification request.
        Sets status to approved and user_type to farmer.
        """
        self.business_permit_status = 'approved'
        if self.user_type == 'buyer':
            self.user_type = 'farmer'
        elif self.user_type not in ['farmer', 'both']:
            self.user_type = 'farmer'
        self.business_permit_updated_at = timezone.now()
        if notes:
            self.business_permit_notes = notes
        self.save()
        
        # Create audit log if approved_by is provided
        if approved_by:
            AuditLog.objects.create(
                actor=approved_by,
                action='verification_approve',
                target_user=self,
                previous_status='pending',
                new_status='approved',
                notes=notes
            )
    
    def reject_farmer_request(self, rejected_by=None, notes=''):
        """
        Reject farmer verification request.
        """
        self.business_permit_status = 'rejected'
        self.business_permit_updated_at = timezone.now()
        self.business_permit_notes = notes
        self.save()
        
        if rejected_by:
            AuditLog.objects.create(
                actor=rejected_by,
                action='verification_reject',
                target_user=self,
                previous_status='pending',
                new_status='rejected',
                notes=notes
            )
    
    def request_reupload(self, requested_by=None, notes=''):
        """
        Request user to reupload their business permit.
        """
        prev_status = self.business_permit_status
        self.business_permit_status = 'none'
        self.business_permit_updated_at = timezone.now()
        self.business_permit_notes = notes
        self.business_permit = None  # Clear the file
        self.save()
        
        if requested_by:
            AuditLog.objects.create(
                actor=requested_by,
                action='verification_reupload',
                target_user=self,
                previous_status=prev_status,
                new_status='none',
                notes=notes
            )
    
    def reset_to_pending(self, reset_by=None, notes=''):
        """
        Reset verification status back to pending.
        """
        prev_status = self.business_permit_status
        self.business_permit_status = 'pending'
        self.business_permit_updated_at = timezone.now()
        if notes:
            self.business_permit_notes = notes
        self.save()
        
        if reset_by:
            AuditLog.objects.create(
                actor=reset_by,
                action='verification_reset',
                target_user=self,
                previous_status=prev_status,
                new_status='pending',
                notes=notes
            )


class AuditLog(models.Model):
    """
    Audit log for tracking staff actions on users and products.
    """
    ACTION_CHOICES = (
        # Verification actions
        ('verification_approve', 'Approved Verification'),
        ('verification_reject', 'Rejected Verification'),
        ('verification_reupload', 'Requested Reupload'),
        ('verification_reset', 'Reset to Pending'),
        # Product actions
        ('product_unlist', 'Unlisted Product'),
        ('product_restore', 'Restored Product'),
        ('product_feature', 'Featured Product'),
        ('product_unfeature', 'Unfeatured Product'),
        # User actions
        ('user_role_change', 'Changed User Role'),
        ('user_deactivate', 'Deactivated User'),
        ('user_reactivate', 'Reactivated User'),
        ('user_clear_sessions', 'Cleared User Sessions'),
    )
    
    actor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='audit_actions',
        help_text='Staff member who performed the action'
    )
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    target_user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        help_text='User affected by this action'
    )
    target_product = models.ForeignKey(
        'products.Product',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        help_text='Product affected by this action'
    )
    previous_status = models.CharField(max_length=50, blank=True)
    new_status = models.CharField(max_length=50, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'audit_logs'
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-created_at']
    
    def __str__(self):
        target = self.target_user or self.target_product or 'N/A'
        return f"{self.actor} - {self.get_action_display()} - {target}"
