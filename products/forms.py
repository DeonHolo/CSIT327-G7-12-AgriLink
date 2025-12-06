from django import forms
from django.db.models import Case, IntegerField, Value, When
from decimal import Decimal
from .models import Category, Product


class ProductForm(forms.ModelForm):
    """
    Form for creating and editing products
    Includes validation for price, stock, and other fields
    """
    UNIT_CHOICES = [
        ('', '---------'),
        ('kg', 'Kilogram (kg)'),
        ('pc', 'Piece (pc)'),
    ]
    
    unit_choice = forms.ChoiceField(
        choices=UNIT_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-control',
            'id': 'unit-choice'
        }),
        label='Unit'
    )
    
    class Meta:
        model = Product
        fields = [
            'name',
            'category',
            'description',
            'price',
            'stock_quantity',
            'location',
            'image',
            'is_active'
        ]
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Fresh Tomatoes'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Describe your product...'
            }),
            'price': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0.00',
                'step': '0.01',
                'min': '0.01',
                'list': 'price-suggestions'
            }),
            'stock_quantity': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': '0',
                'min': '0'
            }),
            'location': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Cebu City'
            }),
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
        labels = {
            'name': 'Product Name',
            'category': 'Category',
            'description': 'Description',
            'price': 'Price (₱)',
            'stock_quantity': 'Stock Quantity',
            'location': 'Location',
            'image': 'Product Image',
            'is_active': 'Available for Sale'
        }
    
    def __init__(self, *args, **kwargs):
        """Initialize form with farmer instance if provided"""
        self.farmer = kwargs.pop('farmer', None)
        super().__init__(*args, **kwargs)
        
        # Mark required fields
        for field_name in ['name', 'category', 'description', 'price', 'stock_quantity']:
            self.fields[field_name].required = True

        # Keep "Others" at the bottom of the category list
        self.fields['category'].queryset = Category.objects.annotate(
            sort_priority=Case(
                When(name='Others', then=Value(1)),
                default=Value(0),
                output_field=IntegerField()
            )
        ).order_by('sort_priority', 'name')
        
        # Populate unit fields if editing existing product
        if self.instance and self.instance.pk:
            current_unit = self.instance.unit
            unit_values = [choice[0] for choice in self.UNIT_CHOICES if choice[0]]
            if current_unit in unit_values:
                self.fields['unit_choice'].initial = current_unit
    
    def clean_price(self):
        """Validate that price is positive"""
        price = self.cleaned_data.get('price')
        if price is not None and price <= Decimal('0'):
            raise forms.ValidationError('Price must be greater than zero.')
        return price
    
    def clean_stock_quantity(self):
        """Validate stock quantity"""
        stock = self.cleaned_data.get('stock_quantity')
        if stock is not None and stock < 0:
            raise forms.ValidationError('Stock quantity cannot be negative.')
        return stock
    
    def clean_name(self):
        """Validate product name"""
        name = self.cleaned_data.get('name')
        if name and len(name.strip()) < 3:
            raise forms.ValidationError('Product name must be at least 3 characters long.')
        return name.strip()
    
    def clean(self):
        """Validate unit selection"""
        cleaned_data = super().clean()
        unit_choice = cleaned_data.get('unit_choice')
        # Validate that a unit is provided
        if not unit_choice:
            raise forms.ValidationError('Please select a unit of measurement.')
        
        cleaned_data['unit'] = unit_choice
        
        return cleaned_data
    
    def save(self, commit=True):
        """Save product with farmer assignment and unit"""
        product = super().save(commit=False)
        if self.farmer:
            product.farmer = self.farmer
        
        # Set the unit field based on choice
        product.unit = self.cleaned_data.get('unit')
        
        if commit:
            product.save()
        return product

