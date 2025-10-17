from django.contrib import admin
from .models import Category, Product


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """
    Admin interface for Category model
    """
    list_display = ['name', 'description', 'created_at']
    search_fields = ['name', 'description']
    ordering = ['name']
    readonly_fields = ['created_at']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    """
    Admin interface for Product model
    """
    list_display = [
        'name', 
        'farmer', 
        'category', 
        'price', 
        'stock_quantity', 
        'is_active', 
        'is_featured',
        'created_at'
    ]
    list_filter = [
        'is_active', 
        'is_featured', 
        'category', 
        'created_at'
    ]
    search_fields = [
        'name', 
        'description', 
        'farmer__username', 
        'location'
    ]
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'total_sales']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('farmer', 'name', 'category', 'description')
        }),
        ('Pricing & Stock', {
            'fields': ('price', 'unit', 'stock_quantity', 'location')
        }),
        ('Status & Features', {
            'fields': ('is_active', 'is_featured', 'total_sales')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('farmer', 'category')
