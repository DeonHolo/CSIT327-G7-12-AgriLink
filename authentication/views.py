from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from .forms import RegistrationForm
from .models import User

def register_view(request):
    """
    Handle user registration
    Task 1.1.2: Connect registration form to database
    Task 1.1.3: Implement form validation (frontend & backend)
    Task 1.1.4: Display success/error messages for registration
    """
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            # Save user to database
            user = form.save()
            
            # Success message
            messages.success(
                request, 
                f'Account created successfully for {user.username}! You can now log in.'
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
        username = request.POST.get('username')
        password = request.POST.get('password')
        remember_me = request.POST.get('remember_me')
        
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
    Home page view
    """
    context = {
        'title': 'Home - AgriLink'
    }
    return render(request, 'home.html', context)
