from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import password_validation
from .models import User
from django.core.exceptions import ValidationError
import os

class RegistrationForm(UserCreationForm):
    """
    Registration form with custom validation
    """
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email'
        })
    )
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your username'
        })
    )
    password1 = forms.CharField(
        label='Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your password'
        }),
        help_text=password_validation.password_validators_help_text_html()
    )
    password2 = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your password'
        })
    )
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
    
    def clean_email(self):
        """
        Validate that the email is unique (backend validation)
        """
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError('This email is already registered.')
        return email
    
    def clean_username(self):
        """
        Validate that the username is unique (backend validation)
        """
        username = self.cleaned_data.get('username')
        if User.objects.filter(username=username).exists():
            raise ValidationError('This username is already taken.')
        return username
    
    def save(self, commit=True):
        """
        Save user with email
        """
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        if commit:
            user.save()
        return user


class ProfileEditForm(forms.ModelForm):
    """
    Form for editing user profile information
    """
    # Single name field (will be split into first_name / last_name on save)
    name = forms.CharField(
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your full name'
        })
    )
    email = forms.EmailField(
        required=True,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your email'
        })
    )
    phone_number = forms.CharField(
        max_length=15,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your phone number'
        })
    )
    user_type = forms.ChoiceField(
        choices=User.USER_TYPES,
        widget=forms.Select(attrs={
            'class': 'form-control'
        })
    )
    
    class Meta:
        model = User
        # Keep model fields here; `name` is a form-only field handled in save()
        fields = ['email', 'phone_number', 'user_type']
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        # Initialize combined name field using user's first/last name
        if self.user:
            full_name = ' '.join(filter(None, [self.user.first_name, self.user.last_name]))
            self.fields['name'].initial = full_name
    
    def clean_email(self):
        """
        Validate that the email is unique (excluding current user)
        """
        email = self.cleaned_data.get('email')
        if self.user:
            if User.objects.filter(email=email).exclude(pk=self.user.pk).exists():
                raise ValidationError('This email is already registered by another user.')
        return email

    def save(self, commit=True):
        """Save profile info and split `name` into first_name and last_name."""
        # Save the model fields handled by ModelForm first
        user = super(forms.ModelForm, self).save(commit=False)

        # Handle the name splitting
        name = self.cleaned_data.get('name', '').strip()
        if name:
            parts = name.split()
            user.first_name = parts[0]
            user.last_name = ' '.join(parts[1:]) if len(parts) > 1 else ''

        if commit:
            user.save()
        return user


class PasswordChangeForm(forms.Form):
    """
    Form for changing user password
    """
    current_password = forms.CharField(
        label='Current Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your current password'
        })
    )
    new_password1 = forms.CharField(
        label='New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter your new password'
        }),
        help_text=password_validation.password_validators_help_text_html()
    )
    new_password2 = forms.CharField(
        label='Confirm New Password',
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'Confirm your new password'
        })
    )
    
    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
    
    def clean_current_password(self):
        """
        Validate that the current password is correct
        """
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise ValidationError('Your current password is incorrect.')
        return current_password
    
    def clean_new_password2(self):
        """
        Validate that the two new passwords match
        """
        password1 = self.cleaned_data.get('new_password1')
        password2 = self.cleaned_data.get('new_password2')
        if password1 and password2 and password1 != password2:
            raise ValidationError('The two password fields did not match.')
        # Validate password strength
        if password2:
            password_validation.validate_password(password2, self.user)
        return password2
    
    def save(self, commit=True):
        """
        Save the new password
        """
        self.user.set_password(self.cleaned_data['new_password1'])
        if commit:
            self.user.save()
        return self.user


class ProfilePictureForm(forms.ModelForm):
    """
    Form for uploading profile picture
    """
    ALLOWED_EXTENSIONS = ['jpg', 'jpeg', 'png', 'gif', 'webp']
    MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
    
    profile_picture = forms.ImageField(
        required=True,
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': 'image/jpeg,image/png,image/gif,image/webp'
        })
    )
    
    class Meta:
        model = User
        fields = ['profile_picture']
    
    def clean_profile_picture(self):
        """
        Validate uploaded image file type and size
        """
        picture = self.cleaned_data.get('profile_picture')
        if picture:
            # Check file extension
            ext = os.path.splitext(picture.name)[1].lower().replace('.', '')
            if ext not in self.ALLOWED_EXTENSIONS:
                raise ValidationError(
                    f'Please upload a valid image file. Allowed formats: {", ".join(self.ALLOWED_EXTENSIONS)}'
                )
            
            # Check file size
            if picture.size > self.MAX_FILE_SIZE:
                raise ValidationError('Image file size must be less than 5MB.')
        
        return picture


class NotificationPreferencesForm(forms.ModelForm):
    """
    Form for updating notification preferences
    """
    notify_chat = forms.BooleanField(
        required=False,
        label='Chat Messages',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    notify_permit_decision = forms.BooleanField(
        required=False,
        label='Business Permit Decisions',
        widget=forms.CheckboxInput(attrs={
            'class': 'form-check-input'
        })
    )
    
    class Meta:
        model = User
        fields = ['notify_chat', 'notify_permit_decision']

