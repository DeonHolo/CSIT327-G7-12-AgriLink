from django import forms
from .models import Product, Category
from decimal import Decimal


class ProductForm(forms.ModelForm):
    """
    Form for creating and editing products
    Includes validation for price, stock, and other fields
    """
    UNIT_CHOICES = [
        ('', '---------'),
        ('kg', 'Kilogram (kg)'),
        ('g', 'Gram (g)'),
        ('lbs', 'Pounds (lbs)'),
        ('pieces', 'Pieces'),
        ('bundles', 'Bundles'),
        ('sacks', 'Sacks'),
        ('crates', 'Crates'),
        ('boxes', 'Boxes'),
        ('dozens', 'Dozens'),
        ('liters', 'Liters (L)'),
        ('other', 'Other (specify below)')
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
    
    unit_custom = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter custom unit',
            'id': 'unit-custom'
        }),
        label='Custom Unit'
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
                'min': '0.01'
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
        
        # Populate unit fields if editing existing product
        if self.instance and self.instance.pk:
            current_unit = self.instance.unit
            # Check if current unit is in predefined choices
            unit_values = [choice[0] for choice in self.UNIT_CHOICES if choice[0]]
            if current_unit in unit_values:
                self.fields['unit_choice'].initial = current_unit
            else:
                self.fields['unit_choice'].initial = 'other'
                self.fields['unit_custom'].initial = current_unit
    
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
        unit_custom = cleaned_data.get('unit_custom')
        
        # Validate that a unit is provided
        if not unit_choice:
            raise forms.ValidationError('Please select a unit of measurement.')
        
        # If "other" is selected, custom unit is required
        if unit_choice == 'other':
            if not unit_custom or not unit_custom.strip():
                raise forms.ValidationError('Please specify a custom unit when "Other" is selected.')
            cleaned_data['unit'] = unit_custom.strip()
        else:
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

