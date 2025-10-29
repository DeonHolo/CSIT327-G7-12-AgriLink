from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Q, Max, Count, Prefetch
from django.core.paginator import Paginator
from .models import Conversation, Message
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
    
    context = {
        'title': f'Chat with {other_user.username} - AgriLink',
        'conversation': conversation,
        'page_obj': page_obj,
        'other_user': other_user,
        'product': conversation.product,
        'last_message_timestamp': last_message_timestamp
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
