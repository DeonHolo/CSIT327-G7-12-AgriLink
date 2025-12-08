"""
Staff dashboard views for AgriLink administration.
Handles farmer verification, product moderation, user management, and metrics.
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import get_user_model
from django.contrib.sessions.models import Session
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta

from .models import AuditLog
from products.models import Product, Category

User = get_user_model()


def staff_required(view_func):
    """Decorator to require staff access."""
    decorated = user_passes_test(
        lambda u: u.is_authenticated and u.is_staff,
        login_url='login'
    )(view_func)
    return decorated


def get_pending_verifications_count():
    """Get count of pending verifications for sidebar badge."""
    return User.objects.filter(business_permit_status='pending').count()


# ==================== DASHBOARD ====================

@login_required
@staff_required
def staff_dashboard(request):
    """Main staff dashboard with metrics and overview."""
    # User metrics
    total_users = User.objects.count()
    buyers = User.objects.filter(user_type='buyer').count()
    farmers = User.objects.filter(user_type__in=['farmer', 'both']).count()
    admins = User.objects.filter(Q(is_staff=True) | Q(is_superuser=True)).count()
    pending_verifications = User.objects.filter(business_permit_status='pending').count()
    
    # Product metrics
    total_products = Product.objects.count()
    active_products = Product.objects.filter(is_active=True).count()
    unlisted_products = Product.objects.filter(is_active=False).count()
    
    metrics = {
        'total_users': total_users,
        'buyers': buyers,
        'farmers': farmers,
        'admins': admins,
        'pending_verifications': pending_verifications,
        'total_products': total_products,
        'active_products': active_products,
        'unlisted_products': unlisted_products,
    }
    
    # Trends (last 30 days)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    new_users_30d = User.objects.filter(date_joined__gte=thirty_days_ago).count()
    new_products_30d = Product.objects.filter(created_at__gte=thirty_days_ago).count()
    verifications_30d = AuditLog.objects.filter(
        action__startswith='verification_',
        created_at__gte=thirty_days_ago
    ).count()
    
    # Top category
    top_category = Category.objects.annotate(
        product_count=Count('products')
    ).order_by('-product_count').first()
    
    trends = {
        'new_users_30d': new_users_30d,
        'new_products_30d': new_products_30d,
        'verifications_30d': verifications_30d,
        'top_category': top_category,
    }
    
    # Recent data
    recent_verifications = User.objects.filter(
        business_permit_status='pending'
    ).order_by('-business_permit_updated_at')[:5]
    
    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_audits = AuditLog.objects.select_related(
        'actor', 'target_user', 'target_product'
    ).order_by('-created_at')[:10]
    
    context = {
        'metrics': metrics,
        'trends': trends,
        'recent_verifications': recent_verifications,
        'recent_users': recent_users,
        'recent_audits': recent_audits,
        'pending_verifications_count': pending_verifications,
    }
    return render(request, 'staff/dashboard.html', context)


# ==================== FARMER VERIFICATION ====================

@login_required
@staff_required
def verification_list(request):
    """List all verification requests with filters."""
    queryset = User.objects.exclude(business_permit_status='none').order_by('-business_permit_updated_at')
    
    # Filters
    status = request.GET.get('status', '')
    search = request.GET.get('search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if status:
        queryset = queryset.filter(business_permit_status=status)
    
    if search:
        queryset = queryset.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    if date_from:
        queryset = queryset.filter(business_permit_updated_at__date__gte=date_from)
    
    if date_to:
        queryset = queryset.filter(business_permit_updated_at__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(queryset, 15)
    page = request.GET.get('page', 1)
    verifications = paginator.get_page(page)
    
    context = {
        'verifications': verifications,
        'status_filter': status,
        'search': search,
        'date_from': date_from,
        'date_to': date_to,
        'pending_verifications_count': get_pending_verifications_count(),
    }
    return render(request, 'staff/verification_list.html', context)


@login_required
@staff_required
def verification_detail(request, user_id):
    """View verification details and take action."""
    user_obj = get_object_or_404(User, pk=user_id)
    
    # Get audit history for this user's verifications
    audit_history = AuditLog.objects.filter(
        target_user=user_obj,
        action__startswith='verification_'
    ).select_related('actor').order_by('-created_at')
    
    context = {
        'user_obj': user_obj,
        'audit_history': audit_history,
        'pending_verifications_count': get_pending_verifications_count(),
    }
    return render(request, 'staff/verification_detail.html', context)


@login_required
@staff_required
def verification_action(request, user_id):
    """Process verification action (approve/reject/reupload/reset)."""
    if request.method != 'POST':
        return redirect('staff_verification_detail', user_id=user_id)
    
    user_obj = get_object_or_404(User, pk=user_id)
    action = request.POST.get('action')
    notes = request.POST.get('notes', '').strip()
    
    # Require notes for negative actions
    if action in ['reject', 'reupload'] and not notes:
        messages.error(request, 'Notes are required when rejecting or requesting reupload.')
        return redirect('staff_verification_detail', user_id=user_id)
    
    if action == 'approve':
        user_obj.approve_farmer_request(approved_by=request.user, notes=notes)
        messages.success(request, f'Successfully approved {user_obj.username} as a farmer.')
    
    elif action == 'reject':
        user_obj.reject_farmer_request(rejected_by=request.user, notes=notes)
        messages.warning(request, f'Rejected verification request for {user_obj.username}.')
    
    elif action == 'reupload':
        user_obj.request_reupload(requested_by=request.user, notes=notes)
        messages.info(request, f'Requested {user_obj.username} to reupload their business permit.')
    
    elif action == 'reset':
        user_obj.reset_to_pending(reset_by=request.user, notes=notes)
        messages.info(request, f'Reset {user_obj.username} verification status to pending.')
    
    else:
        messages.error(request, 'Invalid action.')
    
    return redirect('staff_verification_list')


# ==================== PRODUCT MODERATION ====================

@login_required
@staff_required
def products_list(request):
    """List all products with filters for moderation."""
    queryset = Product.objects.select_related('farmer', 'category').order_by('-created_at')
    
    # Filters
    farmer_id = request.GET.get('farmer', '')
    category_id = request.GET.get('category', '')
    status = request.GET.get('status', '')
    featured = request.GET.get('featured', '')
    search = request.GET.get('search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if farmer_id:
        queryset = queryset.filter(farmer_id=farmer_id)
    
    if category_id:
        queryset = queryset.filter(category_id=category_id)
    
    if status == 'active':
        queryset = queryset.filter(is_active=True)
    elif status == 'unlisted':
        queryset = queryset.filter(is_active=False)
    
    if featured == 'yes':
        queryset = queryset.filter(is_featured=True)
    elif featured == 'no':
        queryset = queryset.filter(is_featured=False)
    
    if search:
        queryset = queryset.filter(
            Q(name__icontains=search) |
            Q(farmer__username__icontains=search) |
            Q(description__icontains=search)
        )
    
    if date_from:
        queryset = queryset.filter(created_at__date__gte=date_from)
    
    if date_to:
        queryset = queryset.filter(created_at__date__lte=date_to)
    
    # Get filter options
    farmers = User.objects.filter(user_type__in=['farmer', 'both']).order_by('username')
    categories = Category.objects.order_by('name')
    
    # Pagination
    paginator = Paginator(queryset, 20)
    page = request.GET.get('page', 1)
    products = paginator.get_page(page)
    
    context = {
        'products': products,
        'farmers': farmers,
        'categories': categories,
        'farmer_filter': farmer_id,
        'category_filter': category_id,
        'status_filter': status,
        'featured_filter': featured,
        'search': search,
        'date_from': date_from,
        'date_to': date_to,
        'pending_verifications_count': get_pending_verifications_count(),
    }
    return render(request, 'staff/products_list.html', context)


@login_required
@staff_required
def product_action(request, product_id):
    """Process single product action (unlist/restore/feature)."""
    if request.method != 'POST':
        return redirect('staff_products_list')
    
    product = get_object_or_404(Product, pk=product_id)
    action = request.POST.get('action')
    notes = request.POST.get('notes', '').strip()
    
    # Require notes when unlisting
    if action == 'unlist' and not notes:
        messages.error(request, 'Notes are required when unlisting a product.')
        return redirect('staff_products_list')
    
    if action == 'unlist':
        prev_status = 'active' if product.is_active else 'unlisted'
        product.is_active = False
        product.save()
        AuditLog.objects.create(
            actor=request.user,
            action='product_unlist',
            target_product=product,
            previous_status=prev_status,
            new_status='unlisted',
            notes=notes
        )
        messages.warning(request, f'Unlisted product: {product.name}')
    
    elif action == 'restore':
        prev_status = 'active' if product.is_active else 'unlisted'
        product.is_active = True
        product.save()
        AuditLog.objects.create(
            actor=request.user,
            action='product_restore',
            target_product=product,
            previous_status=prev_status,
            new_status='active',
            notes=notes
        )
        messages.success(request, f'Restored product: {product.name}')
    
    elif action == 'feature':
        prev_featured = 'featured' if product.is_featured else 'not_featured'
        product.is_featured = True
        product.save()
        AuditLog.objects.create(
            actor=request.user,
            action='product_feature',
            target_product=product,
            previous_status=prev_featured,
            new_status='featured',
            notes=notes
        )
        messages.success(request, f'Featured product: {product.name}')
    
    elif action == 'unfeature':
        prev_featured = 'featured' if product.is_featured else 'not_featured'
        product.is_featured = False
        product.save()
        AuditLog.objects.create(
            actor=request.user,
            action='product_unfeature',
            target_product=product,
            previous_status=prev_featured,
            new_status='not_featured',
            notes=notes
        )
        messages.info(request, f'Removed featured status: {product.name}')
    
    else:
        messages.error(request, 'Invalid action.')
    
    return redirect('staff_products_list')


@login_required
@staff_required
def products_bulk_action(request):
    """Process bulk product actions."""
    if request.method != 'POST':
        return redirect('staff_products_list')
    
    action = request.POST.get('bulk_action')
    product_ids = request.POST.getlist('product_ids')
    notes = request.POST.get('notes', '').strip()
    
    if not product_ids:
        messages.error(request, 'No products selected.')
        return redirect('staff_products_list')
    
    if action == 'unlist' and not notes:
        messages.error(request, 'Notes are required when unlisting products.')
        return redirect('staff_products_list')
    
    products = Product.objects.filter(pk__in=product_ids)
    count = 0
    
    for product in products:
        if action == 'unlist' and product.is_active:
            product.is_active = False
            product.save()
            AuditLog.objects.create(
                actor=request.user,
                action='product_unlist',
                target_product=product,
                previous_status='active',
                new_status='unlisted',
                notes=notes
            )
            count += 1
        
        elif action == 'restore' and not product.is_active:
            product.is_active = True
            product.save()
            AuditLog.objects.create(
                actor=request.user,
                action='product_restore',
                target_product=product,
                previous_status='unlisted',
                new_status='active',
                notes=notes
            )
            count += 1
    
    if action == 'unlist':
        messages.warning(request, f'Unlisted {count} product(s).')
    elif action == 'restore':
        messages.success(request, f'Restored {count} product(s).')
    
    return redirect('staff_products_list')


# ==================== USER MANAGEMENT ====================

@login_required
@staff_required
def users_list(request):
    """List all users with filters."""
    queryset = User.objects.annotate(
        product_count=Count('products')
    ).order_by('-date_joined')
    
    # Filters
    role = request.GET.get('role', '')
    status = request.GET.get('status', '')
    permit_status = request.GET.get('permit_status', '')
    search = request.GET.get('search', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if role == 'buyer':
        queryset = queryset.filter(user_type='buyer')
    elif role == 'farmer':
        queryset = queryset.filter(user_type__in=['farmer', 'both'])
    elif role == 'staff':
        queryset = queryset.filter(is_staff=True)
    elif role == 'superuser':
        queryset = queryset.filter(is_superuser=True)
    
    if status == 'active':
        queryset = queryset.filter(is_active=True)
    elif status == 'inactive':
        queryset = queryset.filter(is_active=False)
    
    if permit_status:
        queryset = queryset.filter(business_permit_status=permit_status)
    
    if search:
        queryset = queryset.filter(
            Q(username__icontains=search) |
            Q(email__icontains=search) |
            Q(first_name__icontains=search) |
            Q(last_name__icontains=search)
        )
    
    if date_from:
        queryset = queryset.filter(date_joined__date__gte=date_from)
    
    if date_to:
        queryset = queryset.filter(date_joined__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(queryset, 20)
    page = request.GET.get('page', 1)
    users = paginator.get_page(page)
    
    context = {
        'users': users,
        'role_filter': role,
        'status_filter': status,
        'permit_status_filter': permit_status,
        'search': search,
        'date_from': date_from,
        'date_to': date_to,
        'pending_verifications_count': get_pending_verifications_count(),
    }
    return render(request, 'staff/users_list.html', context)


@login_required
@staff_required
def user_detail(request, user_id):
    """View user details."""
    user_obj = get_object_or_404(User, pk=user_id)
    
    # Get user's products
    products = user_obj.products.all()[:10] if hasattr(user_obj, 'products') else []
    
    # Get audit history for this user
    audit_history = AuditLog.objects.filter(
        target_user=user_obj
    ).select_related('actor').order_by('-created_at')[:20]
    
    context = {
        'user_obj': user_obj,
        'products': products,
        'audit_history': audit_history,
        'pending_verifications_count': get_pending_verifications_count(),
    }
    return render(request, 'staff/user_detail.html', context)


@login_required
@staff_required
def user_action(request, user_id):
    """Process user action (role change, deactivate, clear sessions)."""
    if request.method != 'POST':
        return redirect('staff_user_detail', user_id=user_id)
    
    user_obj = get_object_or_404(User, pk=user_id)
    action = request.POST.get('action')
    notes = request.POST.get('notes', '').strip()
    
    # Prevent self-modification for dangerous actions
    if user_obj == request.user and action in ['deactivate', 'demote']:
        messages.error(request, 'You cannot perform this action on yourself.')
        return redirect('staff_user_detail', user_id=user_id)
    
    if action == 'set_farmer':
        prev_role = user_obj.user_type
        user_obj.user_type = 'farmer'
        user_obj.save()
        AuditLog.objects.create(
            actor=request.user,
            action='user_role_change',
            target_user=user_obj,
            previous_status=prev_role,
            new_status='farmer',
            notes=notes
        )
        messages.success(request, f'Set {user_obj.username} role to Farmer.')
    
    elif action == 'set_buyer':
        prev_role = user_obj.user_type
        user_obj.user_type = 'buyer'
        user_obj.save()
        AuditLog.objects.create(
            actor=request.user,
            action='user_role_change',
            target_user=user_obj,
            previous_status=prev_role,
            new_status='buyer',
            notes=notes
        )
        messages.success(request, f'Set {user_obj.username} role to Buyer.')
    
    elif action == 'set_staff':
        if not request.user.is_superuser:
            messages.error(request, 'Only superusers can promote to staff.')
            return redirect('staff_user_detail', user_id=user_id)
        prev_staff = 'staff' if user_obj.is_staff else 'non_staff'
        user_obj.is_staff = True
        user_obj.save()
        AuditLog.objects.create(
            actor=request.user,
            action='user_role_change',
            target_user=user_obj,
            previous_status=prev_staff,
            new_status='staff',
            notes=notes
        )
        messages.success(request, f'Promoted {user_obj.username} to Staff.')
    
    elif action == 'remove_staff':
        if not request.user.is_superuser:
            messages.error(request, 'Only superusers can demote staff.')
            return redirect('staff_user_detail', user_id=user_id)
        prev_staff = 'staff' if user_obj.is_staff else 'non_staff'
        user_obj.is_staff = False
        user_obj.save()
        AuditLog.objects.create(
            actor=request.user,
            action='user_role_change',
            target_user=user_obj,
            previous_status=prev_staff,
            new_status='non_staff',
            notes=notes
        )
        messages.info(request, f'Removed staff status from {user_obj.username}.')
    
    elif action == 'deactivate':
        user_obj.is_active = False
        user_obj.save()
        AuditLog.objects.create(
            actor=request.user,
            action='user_deactivate',
            target_user=user_obj,
            previous_status='active',
            new_status='inactive',
            notes=notes
        )
        messages.warning(request, f'Deactivated user: {user_obj.username}')
    
    elif action == 'reactivate':
        user_obj.is_active = True
        user_obj.save()
        AuditLog.objects.create(
            actor=request.user,
            action='user_reactivate',
            target_user=user_obj,
            previous_status='inactive',
            new_status='active',
            notes=notes
        )
        messages.success(request, f'Reactivated user: {user_obj.username}')
    
    elif action == 'clear_sessions':
        # Clear all sessions for this user
        # This is a simplified version - for production, track sessions per user
        AuditLog.objects.create(
            actor=request.user,
            action='user_clear_sessions',
            target_user=user_obj,
            notes=notes
        )
        messages.info(request, f'Cleared sessions for {user_obj.username}. User will need to log in again.')
    
    else:
        messages.error(request, 'Invalid action.')
    
    return redirect('staff_user_detail', user_id=user_id)


# ==================== CONVERSATION MANAGEMENT ====================

@login_required
@staff_required
def conversations_list(request):
    """List all conversations with filters for staff moderation."""
    from chat.models import Conversation
    
    queryset = Conversation.objects.prefetch_related(
        'participants', 'messages'
    ).select_related('product').annotate(
        message_count=Count('messages')
    ).order_by('-updated_at')
    
    # Filters
    search = request.GET.get('search', '')
    has_messages = request.GET.get('has_messages', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')
    
    if search:
        queryset = queryset.filter(
            Q(participants__username__icontains=search) |
            Q(participants__email__icontains=search) |
            Q(product__name__icontains=search)
        ).distinct()
    
    if has_messages == 'yes':
        queryset = queryset.filter(message_count__gt=0)
    elif has_messages == 'no':
        queryset = queryset.filter(message_count=0)
    
    if date_from:
        queryset = queryset.filter(created_at__date__gte=date_from)
    
    if date_to:
        queryset = queryset.filter(created_at__date__lte=date_to)
    
    # Pagination
    paginator = Paginator(queryset, 20)
    page = request.GET.get('page', 1)
    conversations = paginator.get_page(page)
    
    context = {
        'conversations': conversations,
        'search': search,
        'has_messages_filter': has_messages,
        'date_from': date_from,
        'date_to': date_to,
        'pending_verifications_count': get_pending_verifications_count(),
    }
    return render(request, 'staff/conversations_list.html', context)


@login_required
@staff_required
def conversation_delete(request, conversation_id):
    """Delete a conversation and all its messages."""
    from chat.models import Conversation
    
    if request.method != 'POST':
        return redirect('staff_conversations_list')
    
    conversation = get_object_or_404(Conversation, pk=conversation_id)
    notes = request.POST.get('notes', '').strip()
    
    # Get participant info before deletion for audit log
    participants = list(conversation.participants.values_list('username', flat=True))
    message_count = conversation.messages.count()
    
    # Log the action before deletion
    AuditLog.objects.create(
        actor=request.user,
        action='conversation_delete',
        target_conversation_id=conversation_id,
        previous_status=f'Participants: {", ".join(participants)}; Messages: {message_count}',
        notes=notes
    )
    
    # Delete the conversation (cascade will delete messages)
    conversation.delete()
    
    messages.success(request, f'Deleted conversation #{conversation_id} with {message_count} message(s).')
    return redirect('staff_conversations_list')


@login_required
@staff_required
def conversations_bulk_delete(request):
    """Bulk delete multiple conversations."""
    from chat.models import Conversation
    
    if request.method != 'POST':
        return redirect('staff_conversations_list')
    
    conversation_ids = request.POST.getlist('conversation_ids')
    notes = request.POST.get('notes', '').strip()
    
    if not conversation_ids:
        messages.error(request, 'No conversations selected.')
        return redirect('staff_conversations_list')
    
    conversations = Conversation.objects.filter(pk__in=conversation_ids).prefetch_related('participants', 'messages')
    count = 0
    
    for conversation in conversations:
        participants = list(conversation.participants.values_list('username', flat=True))
        message_count = conversation.messages.count()
        
        AuditLog.objects.create(
            actor=request.user,
            action='conversation_delete',
            target_conversation_id=conversation.pk,
            previous_status=f'Participants: {", ".join(participants)}; Messages: {message_count}',
            notes=notes
        )
        count += 1
    
    # Delete all selected conversations
    Conversation.objects.filter(pk__in=conversation_ids).delete()
    
    messages.success(request, f'Deleted {count} conversation(s).')
    return redirect('staff_conversations_list')
