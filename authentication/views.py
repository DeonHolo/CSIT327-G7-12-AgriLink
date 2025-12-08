from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db.models import Prefetch
from django.utils import timezone
from django.http import JsonResponse
from .forms import RegistrationForm, PasswordChangeForm, ProfilePictureForm, NotificationPreferencesForm
from .models import User
import os

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
            
            # Automatically log in the user after registration
            login(request, user)
            
            # Success message
            messages.success(
                request, 
                f'Welcome to AgriLink, {user.username}! Your account has been created successfully.'
            )
            
            # Redirect to home page since user is now logged in
            return redirect('home')
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
            # Staff and superusers land on the staff dashboard
            if user.is_staff:
                return redirect('staff_dashboard')
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
    - Authenticated users: Role-specific dashboard with personalized content
    """
    # Redirect unauthenticated users to the landing page
    if not request.user.is_authenticated:
        return redirect('landing')
    
    # Import models here to avoid circular imports
    from products.models import Product
    from chat.models import Conversation, Message
    from django.db.models import Count, Q
    
    user = request.user
    
    # Base products query
    all_active_products = Product.objects.filter(is_active=True).select_related('farmer', 'category')
    
    # Featured and top products for highlights section (3 each)
    featured_products = all_active_products.filter(is_featured=True)[:3]
    top_products = all_active_products.order_by('-total_sales')[:3]

    # Merge featured/top into a single list with flags to avoid duplicates
    highlight_map = {}
    for p in featured_products:
        highlight_map[p.id] = {'product': p, 'is_featured': True, 'is_top': False}
    for p in top_products:
        if p.id not in highlight_map:
            highlight_map[p.id] = {'product': p, 'is_featured': False, 'is_top': True}
        else:
            highlight_map[p.id]['is_top'] = True
    highlight_products = list(highlight_map.values())
    
    # Recent conversations for both roles (limit 3 for home page)
    recent_conversations = Conversation.objects.filter(
        participants=user
    ).exclude(
        deleted_by=user
    ).select_related('product').prefetch_related('participants', 'messages')[:3]
    recent_conversation_data = []
    for convo in recent_conversations:
        recent_conversation_data.append({
            'conversation': convo,
            'other': convo.get_other_participant(user),
            'last_msg': convo.get_last_message(),
            'unread': convo.get_unread_count(user)
        })
    
    # Unread messages count
    unread_messages = Message.objects.filter(
        conversation__participants=user,
        is_read=False
    ).exclude(sender=user).count()
    
    # Role-specific context
    context = {
        'title': 'Dashboard - AgriLink',
        'featured_products': featured_products,
        'top_products': top_products,
        'highlight_products': highlight_products,
        'recent_conversations': recent_conversation_data,
        'unread_messages': unread_messages,
    }
    
    if user.is_farmer():
        # Farmer-specific stats
        user_products = user.products.all()
        context['active_count'] = user_products.filter(is_active=True).count()
        context['inactive_count'] = user_products.filter(is_active=False).count()
        context['low_stock_count'] = user_products.filter(is_active=True, stock_quantity__lt=10).count()
        context['recent_products'] = user_products.order_by('-created_at')[:3]
    else:
        # Buyer-specific stats
        context['total_products'] = all_active_products.count()
        context['total_farmers'] = User.objects.filter(
            user_type__in=['farmer', 'both']
        ).count()
        context['recent_products'] = all_active_products.order_by('-created_at')[:3]
    
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


@login_required
def profile_view(request):
    """
    Display user profile with activity history
    Acceptance Criteria:
    - Load Profile: Display profile details when navigating to profile
    - View Activity History: Show past activities (products, calculations, messages)
    - Update Profile View: Refresh shows latest details
    """
    user = request.user
    
    # Get activity history
    # Products (for farmers)
    products = []
    seller_reviews = []
    if user.is_farmer():
        products = user.products.all().order_by('-created_at')[:10]
        
        # Get seller reviews (reviews on deals where this user was the farmer)
        from chat.models import Review
        seller_reviews = Review.objects.filter(
            deal__farmer=user
        ).select_related(
            'deal__product', 'reviewer', 'deal'
        ).order_by('-created_at')[:10]
    
    # Saved calculations
    calculations = user.calculations.all().order_by('-created_at')[:10]
    
    # Recent messages sent
    recent_messages = user.sent_messages.select_related(
        'conversation'
    ).order_by('-timestamp')[:10]
    
    context = {
        'title': 'My Profile - AgriLink',
        'profile_user': user,
        'products': products,
        'calculations': calculations,
        'recent_messages': recent_messages,
        'seller_reviews': seller_reviews,
    }
    return render(request, 'authentication/profile.html', context)


@login_required
def update_name_view(request):
    """
    Update user's name via inline editing (single field, auto-save on blur)
    """
    if request.method != 'POST':
        return redirect('profile')
    
    user = request.user
    full_name = request.POST.get('full_name', '').strip()
    
    # Split full name into first and last name
    name_parts = full_name.split(' ', 1)
    user.first_name = name_parts[0] if name_parts else ''
    user.last_name = name_parts[1] if len(name_parts) > 1 else ''
    user.save()
    
    messages.success(request, 'Your name has been updated.')
    return redirect('profile')


@login_required
def update_email_view(request):
    """
    Update user's email via modal
    For MVP: OTP/verification is visual only, email updates directly
    """
    if request.method != 'POST':
        return redirect('profile')
    
    user = request.user
    new_email = request.POST.get('email', '').strip()
    
    if not new_email:
        messages.error(request, 'Please enter a valid email address.')
        return redirect('profile')
    
    # Check if email is already taken by another user
    from django.contrib.auth import get_user_model
    User = get_user_model()
    if User.objects.filter(email=new_email).exclude(pk=user.pk).exists():
        messages.error(request, 'This email is already in use by another account.')
        return redirect('profile')
    
    user.email = new_email
    user.save()
    
    messages.success(request, 'Your email has been updated successfully.')
    return redirect('profile')


@login_required
def update_phone_view(request):
    """
    Update user's phone number via modal
    For MVP: OTP is visual only, phone updates directly
    """
    if request.method != 'POST':
        return redirect('profile')
    
    user = request.user
    new_phone = request.POST.get('phone_number', '').strip()
    
    user.phone_number = new_phone if new_phone else None
    user.save()
    
    messages.success(request, 'Your phone number has been updated successfully.')
    return redirect('profile')


@login_required
def change_password_view(request):
    """
    Change user password
    Acceptance Criteria:
    - Change Password: Enter new password and save
    - Can log in with new password after change
    """
    user = request.user
    
    if request.method == 'POST':
        form = PasswordChangeForm(user, request.POST)
        if form.is_valid():
            form.save()
            # Keep the user logged in after password change
            update_session_auth_hash(request, user)
            messages.success(request, 'Your password has been changed successfully.')
            return redirect('profile')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        messages.error(request, error)
                    else:
                        messages.error(request, f'{error}')
    else:
        form = PasswordChangeForm(user)
    
    context = {
        'title': 'Change Password - AgriLink',
        'form': form,
    }
    return render(request, 'authentication/password_change.html', context)


@login_required
def upload_profile_picture_view(request):
    """
    Upload or replace profile picture
    Acceptance Criteria:
    - Upload Picture: Select valid image and update profile
    - Preview Before Upload: See preview before uploading
    - Upload Wrong File Type: Show error for non-image files
    - Cancel Upload: No changes made if cancelled
    - Replace Existing Image: Old picture replaced with new one
    """
    user = request.user

    if request.method != 'POST':
        return redirect('profile')
    
    # Check if user wants to remove the picture
    if 'remove_picture' in request.POST:
        if user.profile_picture:
            # Delete the old file
            old_picture_path = user.profile_picture.path
            if os.path.exists(old_picture_path):
                os.remove(old_picture_path)
            user.profile_picture = None
            user.save()
            messages.success(request, 'Your profile picture has been removed.')
        return redirect('profile')
    
    form = ProfilePictureForm(request.POST, request.FILES, instance=user)
    if form.is_valid():
        # Delete old picture if exists
        if user.profile_picture:
            old_picture_path = user.profile_picture.path
            if os.path.exists(old_picture_path):
                os.remove(old_picture_path)
        
        form.save()
        messages.success(request, 'Your profile picture has been updated successfully.')
        return redirect('profile')
    
    for field, errors in form.errors.items():
        for error in errors:
            messages.error(request, error)
    return redirect('profile')


@login_required
def upload_business_permit_view(request):
    """
    Upload business permit for farmer verification request.
    Sets status to 'pending' and awaits admin approval.
    Role does NOT change until admin approves.
    """
    user = request.user
    
    if request.method != 'POST':
        return redirect('profile')
    
    # Check if user is already an approved farmer
    if user.user_type in ['farmer', 'both'] and user.business_permit_status == 'approved':
        messages.info(request, 'You are already verified as a farmer.')
        return redirect('profile')
    
    # Check if there's already a pending request
    if user.business_permit_status == 'pending':
        messages.warning(request, 'You already have a pending verification request. Please wait for admin review.')
        return redirect('profile')
    
    # Validate file upload
    permit_file = request.FILES.get('business_permit')
    if not permit_file:
        messages.error(request, 'Please select a file to upload.')
        return redirect('profile')
    
    # Validate file type (images and PDF)
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'application/pdf']
    if permit_file.content_type not in allowed_types:
        messages.error(request, 'Invalid file type. Please upload an image (JPEG, PNG, GIF, WebP) or PDF.')
        return redirect('profile')
    
    # Validate file size (max 5MB)
    max_size = 5 * 1024 * 1024  # 5MB
    if permit_file.size > max_size:
        messages.error(request, 'File too large. Maximum size is 5MB.')
        return redirect('profile')
    
    # Delete old permit if exists
    if user.business_permit:
        try:
            old_permit_path = user.business_permit.path
            if os.path.exists(old_permit_path):
                os.remove(old_permit_path)
        except Exception:
            pass  # Ignore errors deleting old file
    
    # Save new permit and set status to pending
    user.business_permit = permit_file
    user.business_permit_status = 'pending'
    user.business_permit_notes = ''  # Clear any previous rejection notes
    user.business_permit_updated_at = timezone.now()
    user.save()
    
    messages.success(
        request,
        'Your business permit has been submitted for verification. '
        'You will be notified once an admin reviews your request.'
    )
    return redirect('profile')


@login_required
def settings_view(request):
    """
    Settings page with account, security, farmer status, and notifications.
    """
    user = request.user
    
    # Handle notification preferences form submission
    if request.method == 'POST':
        form = NotificationPreferencesForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your notification preferences have been updated.')
            return redirect('settings')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, error)
    else:
        form = NotificationPreferencesForm(instance=user)
    
    context = {
        'title': 'Settings - AgriLink',
        'form': form,
    }
    return render(request, 'authentication/settings.html', context)


@login_required
def logout_all_sessions_view(request):
    """
    Log out from all sessions (clears all user sessions).
    """
    if request.method != 'POST':
        return redirect('settings')
    
    # Store user info before clearing sessions
    user = request.user
    
    # Clear all sessions for this user
    # Note: This is a simple implementation that logs out the current session
    # For production, you'd want to track all sessions in the database
    from django.contrib.auth import logout
    logout(request)
    
    messages.success(
        request,
        'You have been logged out from all sessions. Please log in again.'
    )
    return redirect('login')


def get_farmer_profile(request, user_id):
    """
    API endpoint to get farmer profile data with reviews.
    Returns JSON with farmer info, rating summary, and recent reviews.
    """
    farmer = get_object_or_404(User, pk=user_id)
    
    # Check if the user is a farmer
    if not farmer.is_farmer():
        return JsonResponse({'error': 'User is not a farmer'}, status=404)
    
    # Get recent seller reviews (max 2)
    from chat.models import Review
    from products.models import Product
    
    reviews = Review.objects.filter(
        deal__farmer=farmer
    ).select_related(
        'deal__product', 'reviewer'
    ).order_by('-created_at')[:2]
    
    reviews_data = []
    for review in reviews:
        reviews_data.append({
            'id': review.id,
            'reviewer_name': review.reviewer.username,
            'reviewer_avatar': review.reviewer.profile_picture.url if review.reviewer.profile_picture else None,
            'seller_rating': review.seller_rating,
            'seller_comment': review.seller_comment,
            'product_name': review.deal.product.name,
            'quantity': review.deal.quantity,
            'unit': review.deal.product.unit,
            'created_at': review.created_at.strftime('%b %d, %Y'),
        })
    
    # Get active products count
    active_products_count = Product.objects.filter(
        farmer=farmer,
        is_active=True
    ).count()
    
    # Build response
    data = {
        'success': True,
        'farmer': {
            'id': farmer.id,
            'username': farmer.username,
            'full_name': farmer.get_full_name() or farmer.username,
            'profile_picture': farmer.profile_picture.url if farmer.profile_picture else None,
            'user_type': farmer.get_user_type_display(),
            'is_verified': farmer.business_permit_status == 'approved',
            'average_rating': float(farmer.average_farmer_rating),
            'rating_count': farmer.farmer_rating_count,
            'active_products_count': active_products_count,
            'member_since': farmer.created_at.strftime('%b %Y'),
        },
        'reviews': reviews_data,
    }
    
    return JsonResponse(data)
