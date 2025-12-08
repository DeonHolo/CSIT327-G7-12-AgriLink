from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Max, Count, Prefetch
from django.core.paginator import Paginator
from django.db import transaction
from django.utils import timezone
from django.views.decorators.http import require_POST
from decimal import Decimal
import json
from .models import Conversation, Message, Deal, Review
from products.models import Product


@login_required
def conversation_list(request):
    """
    Display all user's conversations with last message preview
    Implements FR-17 (Recent messages notification)
    """
    # Get all conversations for the current user, excluding ones they've deleted
    conversations = Conversation.objects.filter(
        participants=request.user
    ).exclude(
        deleted_by=request.user
    ).prefetch_related(
        'participants',
        'product'
    ).annotate(
        last_message_time=Max('messages__timestamp')
    ).order_by('-last_message_time')
    
    # Calculate unread counts and get last messages for each conversation
    conversation_data = []
    total_unread = 0
    for conv in conversations:
        unread_count = conv.get_unread_count(request.user)
        total_unread += unread_count
        last_message = conv.messages.order_by('-timestamp').first()
        conversation_data.append({
            'conversation': conv,
            'other_user': conv.get_other_participant(request.user),
            'last_message': last_message,
            'unread_count': unread_count
        })
    
    context = {
        'title': 'Messages - AgriLink',
        'conversation_data': conversation_data,
        'total_unread': total_unread
    }
    return render(request, 'chat/conversation_list.html', context)


@login_required
def conversation_detail(request, pk):
    """
    Display full message history with pagination
    Implements FR-15 (Chat history with timestamp)
    """
    conversation = get_object_or_404(
        Conversation.objects.prefetch_related('participants', 'product'),
        pk=pk
    )
    
    # Check if user is a participant
    if request.user not in conversation.participants.all():
        messages.error(request, 'You do not have access to this conversation.')
        return redirect('conversation_list')
    
    # Get messages in this conversation (optimized query)
    message_list = conversation.messages.select_related('sender').order_by('timestamp')
    
    # Mark all messages from other user as read
    conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    
    # Pagination (30 messages per page for better performance)
    paginator = Paginator(message_list, 30)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get the other participant
    other_user = conversation.get_other_participant(request.user)
    
    # Get last message timestamp for polling
    last_message = message_list.last()
    last_message_timestamp = last_message.timestamp.isoformat() if last_message else ''
    
    # Get deals in this conversation
    deals = conversation.deals.select_related(
        'product', 'farmer', 'buyer', 'cancelled_by'
    ).prefetch_related('review').order_by('created_at')
    
    # Check if current user is a farmer (can create offers)
    is_farmer = request.user.is_farmer()
    
    # Get farmer's active products for the offer form (if user is a farmer)
    farmer_products = []
    if is_farmer:
        farmer_products = Product.objects.filter(
            farmer=request.user,
            is_active=True,
            stock_quantity__gt=0
        ).values('id', 'name', 'price', 'unit', 'stock_quantity', 'image')
    
    context = {
        'title': f'Chat with {other_user.username} - AgriLink',
        'conversation': conversation,
        'page_obj': page_obj,
        'other_user': other_user,
        'product': conversation.product,
        'last_message_timestamp': last_message_timestamp,
        'deals': deals,
        'is_farmer': is_farmer,
        'farmer_products': list(farmer_products),
    }
    return render(request, 'chat/conversation_detail.html', context)


@login_required
def message_send(request, pk):
    """
    Handle message sending (AJAX endpoint)
    Implements FR-16 (Quick action buttons: Order Now, Request Price)
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    conversation = get_object_or_404(Conversation, pk=pk)
    
    # Check if user is a participant
    if request.user not in conversation.participants.all():
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    content = request.POST.get('content', '').strip()
    message_type = request.POST.get('message_type', 'text')
    
    if not content:
        return JsonResponse({'error': 'Message content cannot be empty'}, status=400)
    
    # Create the message
    message = Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=content,
        message_type=message_type
    )
    
    # Update conversation's updated_at timestamp
    conversation.save()
    
    return JsonResponse({
        'success': True,
        'message': {
            'id': message.id,
            'content': message.content,
            'sender': message.sender.username,
            'sender_id': message.sender.id,
            'timestamp': message.timestamp.isoformat(),
            'timestamp_display': message.timestamp.strftime('%b %d, %Y %I:%M %p'),
            'message_type': message.message_type,
            'message_type_display': message.get_message_type_display()
        }
    })


@login_required
def get_new_messages(request, pk, after_timestamp):
    """
    Get new messages after a specific timestamp (for polling)
    Returns JSON with new messages for real-time updates
    """
    conversation = get_object_or_404(Conversation, pk=pk)
    
    # Check if user is a participant
    if request.user not in conversation.participants.all():
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    try:
        # Parse the timestamp
        from django.utils.dateparse import parse_datetime
        after_dt = parse_datetime(after_timestamp)
        
        if not after_dt:
            return JsonResponse({'error': 'Invalid timestamp format'}, status=400)
        
        # Get messages after the given timestamp
        new_messages = conversation.messages.filter(
            timestamp__gt=after_dt
        ).select_related('sender').order_by('timestamp')
        
        # Mark new messages as read if they're not from current user
        new_messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
        
        # Build message data
        messages_data = []
        for message in new_messages:
            messages_data.append({
                'id': message.id,
                'content': message.content,
                'sender': message.sender.username,
                'sender_id': message.sender.id,
                'timestamp': message.timestamp.isoformat(),
                'timestamp_display': message.timestamp.strftime('%b %d, %Y %I:%M %p'),
                'message_type': message.message_type,
                'message_type_display': message.get_message_type_display()
            })
        
        return JsonResponse({
            'success': True,
            'messages': messages_data,
            'count': len(messages_data)
        })
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def mark_messages_read(request, pk):
    """
    Mark all messages in a conversation as read
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    conversation = get_object_or_404(Conversation, pk=pk)
    
    # Check if user is a participant
    if request.user not in conversation.participants.all():
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Mark all unread messages from other user as read
    updated_count = conversation.messages.filter(
        is_read=False
    ).exclude(
        sender=request.user
    ).update(is_read=True)
    
    return JsonResponse({
        'success': True,
        'marked_read': updated_count
    })


@login_required
def start_conversation(request, product_pk):
    """
    Start or continue conversation about a product
    Links "Contact Seller" button to chat (FR-16)
    """
    product = get_object_or_404(Product, pk=product_pk)
    
    # Check if user is trying to message themselves
    if request.user == product.farmer:
        messages.error(request, 'You cannot message yourself about your own product.')
        return redirect('product_detail', pk=product_pk)
    
    # Check if conversation already exists between these users for this product
    existing_conversation = Conversation.objects.filter(
        participants=request.user
    ).filter(
        participants=product.farmer
    ).filter(
        product=product
    ).first()
    
    if existing_conversation:
        # If user had deleted this conversation, restore it
        if existing_conversation.is_deleted_by(request.user):
            existing_conversation.restore_for_user(request.user)
        # Redirect to existing conversation
        return redirect('conversation_detail', pk=existing_conversation.pk)
    
    # Create new conversation
    conversation = Conversation.objects.create(product=product)
    conversation.participants.add(request.user, product.farmer)
    
    # Create initial system message
    initial_message = f"Started conversation about {product.name}"
    Message.objects.create(
        conversation=conversation,
        sender=request.user,
        content=initial_message,
        message_type='text'
    )
    
    messages.success(request, f'Started conversation with {product.farmer.username}')
    return redirect('conversation_detail', pk=conversation.pk)


@login_required
def delete_conversation(request, pk):
    """
    Delete conversation for the current user only
    The other participant will still see the conversation
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    conversation = get_object_or_404(Conversation, pk=pk)
    
    # Check if user is a participant
    if request.user not in conversation.participants.all():
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Mark conversation as deleted for this user
    conversation.delete_for_user(request.user)
    
    return JsonResponse({
        'success': True,
        'message': 'Conversation deleted'
    })


# =============================================================================
# Deal Management Views
# =============================================================================

@login_required
def get_farmer_products(request, pk):
    """
    Get farmer's active products for the create offer form.
    Returns JSON list of products.
    """
    conversation = get_object_or_404(Conversation, pk=pk)
    
    # Check if user is a participant
    if request.user not in conversation.participants.all():
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Check if user is a farmer
    if not request.user.is_farmer():
        return JsonResponse({'error': 'Only farmers can access this'}, status=403)
    
    # Get farmer's active products with stock
    products = Product.objects.filter(
        farmer=request.user,
        is_active=True,
        stock_quantity__gt=0
    )
    
    products_data = []
    for product in products:
        products_data.append({
            'id': product.id,
            'name': product.name,
            'price': str(product.price),
            'unit': product.unit,
            'stock_quantity': product.stock_quantity,
            'image': product.image.url if product.image else None,
        })
    
    return JsonResponse({
        'success': True,
        'products': products_data
    })


@login_required
@require_POST
def create_offer(request, pk):
    """
    Farmer creates a new deal offer in the conversation.
    """
    conversation = get_object_or_404(Conversation, pk=pk)
    
    # Check if user is a participant
    if request.user not in conversation.participants.all():
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    # Check if user is a farmer
    if not request.user.is_farmer():
        return JsonResponse({'error': 'Only farmers can create offers'}, status=403)
    
    try:
        # Parse request data
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        
        product_id = data.get('product_id')
        quantity = int(data.get('quantity', 0))
        total_price = data.get('total_price')
        
        if not product_id or quantity <= 0:
            return JsonResponse({'error': 'Invalid product or quantity'}, status=400)
        
        # Get the product
        product = get_object_or_404(Product, pk=product_id, farmer=request.user)
        
        # Validate stock
        if product.stock_quantity < quantity:
            return JsonResponse({
                'error': f'Not enough stock. Only {product.stock_quantity} {product.unit} available.'
            }, status=400)
        
        # Calculate total price (or use override)
        calculated_total = product.price * quantity
        if total_price:
            total_price = Decimal(str(total_price))
        else:
            total_price = calculated_total
        
        # Get the buyer (other participant)
        buyer = conversation.get_other_participant(request.user)
        if not buyer:
            return JsonResponse({'error': 'No buyer found in conversation'}, status=400)
        
        # Create the deal
        deal = Deal.objects.create(
            conversation=conversation,
            product=product,
            farmer=request.user,
            buyer=buyer,
            quantity=quantity,
            unit_price=product.price,
            total_price=total_price,
            status='pending'
        )
        
        # Update conversation timestamp
        conversation.save()
        
        return JsonResponse({
            'success': True,
            'deal': _serialize_deal(deal, request.user)
        })
        
    except (ValueError, json.JSONDecodeError) as e:
        return JsonResponse({'error': f'Invalid data: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def accept_deal(request, deal_id):
    """
    Buyer accepts a deal offer. Reserves stock atomically.
    """
    deal = get_object_or_404(Deal, pk=deal_id)
    
    # Only buyer can accept
    if request.user != deal.buyer:
        return JsonResponse({'error': 'Only the buyer can accept this deal'}, status=403)
    
    # Check if deal can be accepted
    if not deal.can_be_accepted():
        return JsonResponse({'error': 'This deal cannot be accepted'}, status=400)
    
    try:
        with transaction.atomic():
            # Lock the product row for update
            product = Product.objects.select_for_update().get(pk=deal.product_id)
            
            # Check stock availability
            if product.stock_quantity < deal.quantity:
                return JsonResponse({
                    'error': 'Sold Out - Not enough stock available',
                    'available': product.stock_quantity
                }, status=400)
            
            # Reserve stock
            product.stock_quantity -= deal.quantity
            product.save(update_fields=['stock_quantity'])
            
            # Update deal status
            deal.status = 'confirmed'
            deal.confirmed_at = timezone.now()
            deal.save(update_fields=['status', 'confirmed_at'])
        
        return JsonResponse({
            'success': True,
            'deal': _serialize_deal(deal, request.user)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def decline_deal(request, deal_id):
    """
    Buyer declines a deal offer.
    """
    deal = get_object_or_404(Deal, pk=deal_id)
    
    # Only buyer can decline
    if request.user != deal.buyer:
        return JsonResponse({'error': 'Only the buyer can decline this deal'}, status=403)
    
    # Check if deal is pending
    if deal.status != 'pending':
        return JsonResponse({'error': 'This deal cannot be declined'}, status=400)
    
    deal.status = 'declined'
    deal.save(update_fields=['status'])
    
    return JsonResponse({
        'success': True,
        'deal': _serialize_deal(deal, request.user)
    })


@login_required
@require_POST
def cancel_deal(request, deal_id):
    """
    Cancel a deal. Farmer can cancel pending offers.
    Either party can cancel confirmed orders (restores stock).
    """
    deal = get_object_or_404(Deal, pk=deal_id)
    
    # Check if user can cancel
    if not deal.can_be_cancelled(request.user):
        return JsonResponse({'error': 'You cannot cancel this deal'}, status=403)
    
    try:
        with transaction.atomic():
            # If deal was confirmed, restore stock
            if deal.status == 'confirmed':
                product = Product.objects.select_for_update().get(pk=deal.product_id)
                product.stock_quantity += deal.quantity
                product.save(update_fields=['stock_quantity'])
            
            # Update deal status
            deal.status = 'cancelled'
            deal.cancelled_by = request.user
            deal.save(update_fields=['status', 'cancelled_by'])
        
        return JsonResponse({
            'success': True,
            'deal': _serialize_deal(deal, request.user)
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
@require_POST
def complete_deal(request, deal_id):
    """
    Buyer marks deal as completed (received the order).
    Returns deal data for showing review modal.
    """
    deal = get_object_or_404(Deal, pk=deal_id)
    
    # Only buyer can complete
    if not deal.can_be_completed(request.user):
        return JsonResponse({'error': 'You cannot complete this deal'}, status=403)
    
    # Update deal status
    deal.status = 'completed'
    deal.completed_at = timezone.now()
    deal.save(update_fields=['status', 'completed_at'])
    
    # Update product's total sales
    deal.product.total_sales += deal.quantity
    deal.product.save(update_fields=['total_sales'])
    
    return JsonResponse({
        'success': True,
        'deal': _serialize_deal(deal, request.user),
        'show_review_modal': True,
        'review_data': {
            'deal_id': deal.id,
            'product_name': deal.product.name,
            'farmer_name': deal.farmer.username,
        }
    })


@login_required
@require_POST
def submit_review(request, deal_id):
    """
    Buyer submits a dual review (seller + product) for a completed deal.
    """
    deal = get_object_or_404(Deal, pk=deal_id)
    
    # Only buyer can review
    if request.user != deal.buyer:
        return JsonResponse({'error': 'Only the buyer can review this deal'}, status=403)
    
    # Check if deal is completed
    if deal.status != 'completed':
        return JsonResponse({'error': 'Can only review completed deals'}, status=400)
    
    # Check if already reviewed
    if deal.is_reviewed:
        return JsonResponse({'error': 'This deal has already been reviewed'}, status=400)
    
    try:
        data = json.loads(request.body) if request.content_type == 'application/json' else request.POST
        
        seller_rating = int(data.get('seller_rating', 0))
        seller_comment = data.get('seller_comment', '').strip()
        product_rating = int(data.get('product_rating', 0))
        product_comment = data.get('product_comment', '').strip()
        
        # Validate ratings
        if not (1 <= seller_rating <= 5) or not (1 <= product_rating <= 5):
            return JsonResponse({'error': 'Ratings must be between 1 and 5'}, status=400)
        
        # Create review (save() method updates aggregate ratings)
        review = Review.objects.create(
            deal=deal,
            reviewer=request.user,
            seller_rating=seller_rating,
            seller_comment=seller_comment,
            product_rating=product_rating,
            product_comment=product_comment
        )
        
        return JsonResponse({
            'success': True,
            'review': {
                'id': review.id,
                'seller_rating': review.seller_rating,
                'seller_comment': review.seller_comment,
                'product_rating': review.product_rating,
                'product_comment': review.product_comment,
            },
            'deal': _serialize_deal(deal, request.user)
        })
        
    except (ValueError, json.JSONDecodeError) as e:
        return JsonResponse({'error': f'Invalid data: {str(e)}'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def get_deal(request, deal_id):
    """
    Get deal details for AJAX polling.
    """
    deal = get_object_or_404(Deal, pk=deal_id)
    
    # Check if user is involved in this deal
    if request.user not in [deal.farmer, deal.buyer]:
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    return JsonResponse({
        'success': True,
        'deal': _serialize_deal(deal, request.user)
    })


@login_required
def get_conversation_deals(request, pk):
    """
    Get all deals in a conversation for AJAX polling.
    """
    conversation = get_object_or_404(Conversation, pk=pk)
    
    # Check if user is a participant
    if request.user not in conversation.participants.all():
        return JsonResponse({'error': 'Access denied'}, status=403)
    
    deals = conversation.deals.select_related(
        'product', 'farmer', 'buyer'
    ).prefetch_related('review').order_by('created_at')
    
    deals_data = [_serialize_deal(deal, request.user) for deal in deals]
    
    return JsonResponse({
        'success': True,
        'deals': deals_data
    })


def _serialize_deal(deal, user):
    """
    Serialize a deal object to JSON-compatible dict.
    """
    is_farmer = user == deal.farmer
    is_buyer = user == deal.buyer
    
    data = {
        'id': deal.id,
        'product': {
            'id': deal.product.id,
            'name': deal.product.name,
            'image': deal.product.image.url if deal.product.image else None,
            'unit': deal.product.unit,
        },
        'farmer': {
            'id': deal.farmer.id,
            'username': deal.farmer.username,
            'profile_picture': deal.farmer.profile_picture.url if deal.farmer.profile_picture else None,
        },
        'buyer': {
            'id': deal.buyer.id,
            'username': deal.buyer.username,
        },
        'quantity': deal.quantity,
        'unit_price': str(deal.unit_price),
        'total_price': str(deal.total_price),
        'status': deal.status,
        'status_display': deal.get_status_display(),
        'created_at': deal.created_at.isoformat(),
        'created_at_display': deal.created_at.strftime('%b %d, %Y %I:%M %p'),
        'confirmed_at': deal.confirmed_at.isoformat() if deal.confirmed_at else None,
        'completed_at': deal.completed_at.isoformat() if deal.completed_at else None,
        'is_farmer': is_farmer,
        'is_buyer': is_buyer,
        'can_accept': deal.can_be_accepted() and is_buyer,
        'can_cancel': deal.can_be_cancelled(user),
        'can_complete': deal.can_be_completed(user),
        'is_reviewed': deal.is_reviewed,
    }
    
    if deal.cancelled_by:
        data['cancelled_by'] = {
            'id': deal.cancelled_by.id,
            'username': deal.cancelled_by.username,
        }
    
    if deal.is_reviewed:
        review = deal.review
        data['review'] = {
            'seller_rating': review.seller_rating,
            'seller_comment': review.seller_comment,
            'product_rating': review.product_rating,
            'product_comment': review.product_comment,
            'created_at': review.created_at.isoformat(),
        }
    
    return data
