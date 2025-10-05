from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .forms import RegistrationForm
from .models import User

def register_view(request):
    """
    Handle user registration with toggle-based role selection
    Task 1.1.2: Connect registration form to database
    Task 1.1.3: Implement form validation (frontend & backend)
    Task 1.1.4: Display success/error messages for registration
    """
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        user_type = request.POST.get('user_type', 'buyer')  # Default to buyer if not specified
        
        if form.is_valid():
            # Save user to database with specified user_type
            user = form.save(commit=False)
            user.user_type = user_type
            user.save()
            
            # Success message with role
            messages.success(
                request, 
                f'{user.get_user_type_display()} account created successfully for {user.username}! You can now log in.'
            )
            
            # Redirect to login page
            return redirect('login')
        else:
            # Display error messages for each field
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = RegistrationForm()
    
    context = {
        'form': form,
        'title': 'Register - AgriLink'
    }
    return render(request, 'authentication/register.html', context)


def login_view(request):
    """
    Handle user login
    Task 1.2.2: Connect login form to authentication API
    """
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        remember_me = request.POST.get('remember_me')
        
        # Validate input
        if not username or not password:
            messages.error(request, 'Both username and password are required.')
            return render(request, 'authentication/login.html', context)
        
        # Authenticate user
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            # Login successful
            login(request, user)
            
            # Handle remember me
            if not remember_me:
                request.session.set_expiry(0)  # Session expires when browser closes
            
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    context = {
        'title': 'Login - AgriLink'
    }
    return render(request, 'authentication/login.html', context)


@login_required
def logout_view(request):
    """
    Handle user logout
    """
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')


def home_view(request):
    """
    Home page view - context-aware based on authentication
    - Guests: Redirected to landing page (marketing content)
    - Authenticated users: Dashboard with personalized content
    """
    # Redirect unauthenticated users to the landing page
    if not request.user.is_authenticated:
        return redirect('landing')
    
    context = {
        'title': 'Dashboard - AgriLink'
    }
    return render(request, 'home.html', context)


def landing_view(request):
    """
    Landing page view
    """
    context = {
        'title': 'Welcome - AgriLink'
    }
    return render(request, 'landing.html', context)


def password_reset_view(request):
    """
    Password reset request view
    """
    if request.method == 'POST':
        email = request.POST.get('email')
        # TODO: Implement actual password reset email sending
        # Always show the same message for security (don't reveal if email exists)
        messages.success(
            request,
            'If an account exists with this email, password reset instructions have been sent.'
        )
        return redirect('login')
    
    context = {
        'title': 'Reset Password - AgriLink'
    }
    return render(request, 'authentication/password_reset.html', context)