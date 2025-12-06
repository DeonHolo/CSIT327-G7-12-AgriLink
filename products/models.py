from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator
from decimal import Decimal

User = get_user_model()


class Category(models.Model):
    """
    Product categories for organizing agricultural products
    """
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        db_table = 'categories'
        verbose_name = 'Category'
        verbose_name_plural = 'Categories'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class Product(models.Model):
    """
    Agricultural products listed by farmers
    Covers FR-6 to FR-11 (Product listing requirements)
    """
    farmer = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='products',
        limit_choices_to={'user_type__in': ['farmer', 'both']}
    )
    name = models.CharField(max_length=200, help_text='Product/crop name')
    category = models.ForeignKey(
        Category, 
        on_delete=models.CASCADE, 
        related_name='products'
    )
    description = models.TextField(help_text='Detailed product description')
    price = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Price per unit'
    )
    unit = models.CharField(
        max_length=50, 
        help_text='Unit of measurement (e.g., kg, pieces, bundles)'
    )
    stock_quantity = models.PositiveIntegerField(
        help_text='Available quantity in stock'
    )
    location = models.CharField(
        max_length=100, 
        blank=True,
        help_text='Product location/farm location'
    )
    image = models.ImageField(
        upload_to='products/',
        blank=True,
        null=True,
        help_text='Product image'
    )
    is_active = models.BooleanField(
        default=True,
        help_text='Whether product is currently available for sale'
    )
    is_featured = models.BooleanField(
        default=False,
        help_text='Featured/advertised products (FR-11)'
    )
    total_sales = models.PositiveIntegerField(
        default=0,
        help_text='Total units sold (for "Top Products" - FR-11)'
    )
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'products'
        verbose_name = 'Product'
        verbose_name_plural = 'Products'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['is_active', 'is_featured']),
            models.Index(fields=['category', 'is_active']),
            models.Index(fields=['is_active']),  # For main product listing query
            models.Index(fields=['farmer', 'is_active']),  # For farmer's products
            models.Index(fields=['price']),  # For price sorting
            models.Index(fields=['total_sales']),  # For top products query
        ]
    
    def __str__(self):
        return f"{self.name} by {self.farmer.username}"
    
    def is_in_stock(self):
        """Check if product has available stock"""
        return self.is_active and self.stock_quantity > 0
    
    def get_stock_status(self):
        """Return stock status message"""
        if not self.is_active:
            return "Unavailable"
        elif self.stock_quantity == 0:
            return "Out of Stock"
        elif self.stock_quantity < 10:
            return f"Low Stock ({self.stock_quantity} {self.unit} left)"
        else:
            return f"In Stock ({self.stock_quantity} {self.unit} available)"


class SavedCalculation(models.Model):
    """
    Saved fair price calculations for users (Feature 6.2)
    Stores calculation history using Market Split Model
    """
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='calculations'
    )
    crop_name = models.CharField(max_length=200)
    category = models.CharField(
        max_length=150,
        blank=True,
        help_text='Category selected during calculation'
    )
    farmgate_price = models.DecimalField(max_digits=10, decimal_places=2)
    market_price = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text='Current price in markets/malls (optional)'
    )
    fair_price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'saved_calculations'
        verbose_name = 'Saved Calculation'
        verbose_name_plural = 'Saved Calculations'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.crop_name} - ₱{self.fair_price} ({self.user.username})"
