from django.db import models
from django.contrib.auth.models import AbstractUser

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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False)
    
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
