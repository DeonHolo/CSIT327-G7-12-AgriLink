from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Case, When, Value, IntegerField
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from decimal import Decimal, InvalidOperation
from .models import Product, Category, SavedCalculation
from .forms import ProductForm
from .utils import calculate_fair_price, calculate_buyer_savings


def _get_price_suggestions(user, limit=5):
    """
    Safely fetch recent saved calculations for price suggestions,
    skipping any rows with invalid decimal values.
    """
    qs = SavedCalculation.objects.filter(user=user).only(
        'id', 'crop_name', 'category', 'fair_price', 'created_at'
    ).order_by('-created_at')[:limit]

    suggestions = []
    for calc in qs:
        try:
            _ = calc.fair_price + Decimal('0')
            suggestions.append(calc)
        except (InvalidOperation, TypeError):
            continue
    return suggestions


def product_list(request):
    """
    Display all active products in grid layout with search and filtering
    Implements FR-10, FR-12, FR-13 (product display, search, filters)
    """
    products = Product.objects.filter(is_active=True).select_related('farmer', 'category')
    
    # Search functionality (FR-12: search by crop, seller, location)
    search_query = request.GET.get('search', '').strip()
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(farmer__username__icontains=search_query) |
            Q(location__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Filter by category (FR-13)
    category_id = request.GET.get('category')
    if category_id:
        products = products.filter(category_id=category_id)
    
    # Filter by price range (FR-13)
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        try:
            products = products.filter(price__gte=float(min_price))
        except ValueError:
            pass
    if max_price:
        try:
            products = products.filter(price__lte=float(max_price))
        except ValueError:
            pass
    
    # Sorting
    sort_by = request.GET.get('sort', '-created_at')
    valid_sorts = ['-created_at', 'created_at', 'price', '-price', 'name', 'popularity']
    if sort_by == 'popularity':
        products = products.order_by('-total_sales')
    elif sort_by in valid_sorts:
        products = products.order_by(sort_by)
    
    # Use paginator's count method for better performance
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    total_results = paginator.count

    # Get all categories for filter sidebar (cached)
    categories = Category.objects.all()
    
    # Get top 3 product IDs by sales for badge display
    top_product_ids = list(
        Product.objects.filter(is_active=True)
        .order_by('-total_sales')
        .values_list('id', flat=True)[:3]
    )

    context = {
        'title': 'Browse Products - AgriLink',
        'page_obj': page_obj,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
        'total_results': total_results,
        'top_product_ids': top_product_ids,
    }
    return render(request, 'products/product_list.html', context)


def product_detail(request, pk):
    """
    Display detailed information about a specific product
    Implements FR-10 (view product details)
    """
    product = get_object_or_404(
        Product.objects.select_related('farmer', 'category'),
        pk=pk
    )

    # Get other products from same farmer (max 4)
    other_products = Product.objects.filter(
        farmer=product.farmer,
        is_active=True
    ).exclude(pk=pk)[:4]

    # Count farmer's active products
    farmer_active_products_count = Product.objects.filter(
        farmer=product.farmer,
        is_active=True
    ).count()
    
    # Get product reviews (reviews on deals for this product)
    from chat.models import Review
    from django.db.models import Count
    
    # Get all reviews for this product
    all_product_reviews = Review.objects.filter(
        deal__product=product
    ).select_related(
        'deal', 'reviewer'
    ).order_by('-created_at')
    
    # Get featured review (highest rated among recent, or just the latest highest)
    featured_review = all_product_reviews.order_by('-product_rating', '-created_at').first()
    
    # Calculate rating distribution for the bars
    rating_distribution = {5: 0, 4: 0, 3: 0, 2: 0, 1: 0}
    for review in all_product_reviews:
        if review.product_rating in rating_distribution:
            rating_distribution[review.product_rating] += 1

    context = {
        'title': f'{product.name} - AgriLink',
        'product': product,
        'other_products': other_products,
        'farmer_active_products_count': farmer_active_products_count,
        'featured_review': featured_review,
        'all_product_reviews': all_product_reviews,
        'rating_distribution': rating_distribution,
    }
    return render(request, 'products/product_detail.html', context)


@login_required
def product_create(request):
    """
    Form for farmers to add new products
    Implements FR-6 (create product listing)
    Only accessible to farmers
    """
    # Check if user is a farmer
    if not request.user.is_farmer():
        messages.error(request, 'Only farmers can add products.')
        return redirect('product_list')
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, farmer=request.user)
        if form.is_valid():
            product = form.save()
            messages.success(
                request, 
                f'Product "{product.name}" has been added successfully!'
            )
            return redirect('product_detail', pk=product.pk)
        else:
            # Display form errors
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = ProductForm()
    
    # Saved calculations to help with price suggestions (defensive fetch)
    price_suggestions = _get_price_suggestions(request.user)
    
    context = {
        'title': 'Add New Product - AgriLink',
        'form': form,
        'action': 'Add',
        'price_suggestions': price_suggestions
    }
    return render(request, 'products/product_form.html', context)


@login_required
def product_edit(request, pk):
    """
    Form for farmers to edit their existing products
    Implements FR-7 (edit product listing)
    Only product owner or admin can edit
    """
    product = get_object_or_404(Product, pk=pk)
    
    # Check permissions
    if product.farmer != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to edit this product.')
        return redirect('product_detail', pk=pk)
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES, instance=product, farmer=request.user)
        if form.is_valid():
            product = form.save()
            messages.success(request, f'Product "{product.name}" has been updated successfully!')
            return redirect('product_detail', pk=product.pk)
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = ProductForm(instance=product)
    
    price_suggestions = _get_price_suggestions(request.user)
    
    context = {
        'title': f'Edit {product.name} - AgriLink',
        'form': form,
        'product': product,
        'action': 'Edit',
        'price_suggestions': price_suggestions
    }
    return render(request, 'products/product_form.html', context)


@login_required
def product_delete(request, pk):
    """
    Delete product listing (requires product to be inactive/unlisted first for regular users).
    Staff can delete products directly without unlisting.
    Also supports unlisting (setting inactive) when action=unlist.
    Only product owner or admin can delete.
    """
    product = get_object_or_404(Product, pk=pk)
    
    # Check permissions
    if product.farmer != request.user and not request.user.is_staff:
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': False, 'error': 'You do not have permission to delete this product.'}, status=403)
        messages.error(request, 'You do not have permission to delete this product.')
        return redirect('product_detail', pk=pk)
    
    if request.method == 'POST':
        action = request.POST.get('action') or request.POST.get('mode')
        is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'

        # Unlist request
        if action == 'unlist':
            if product.is_active:
                product.is_active = False
                product.save(update_fields=['is_active'])
                if is_ajax:
                    return JsonResponse({'success': True, 'message': f'Product "{product.name}" has been unlisted.'})
                messages.success(request, f'Product "{product.name}" has been unlisted.')
            else:
                if is_ajax:
                    return JsonResponse({'success': True, 'message': f'Product "{product.name}" is already inactive.'})
                messages.info(request, f'Product "{product.name}" is already inactive.')
            return redirect('product_detail', pk=pk)

        # Relist request
        if action == 'relist':
            if not product.is_active:
                product.is_active = True
                product.save(update_fields=['is_active'])
                if is_ajax:
                    return JsonResponse({'success': True, 'message': f'Product "{product.name}" has been relisted.'})
                messages.success(request, f'Product "{product.name}" has been relisted and is now visible to buyers.')
            else:
                if is_ajax:
                    return JsonResponse({'success': True, 'message': f'Product "{product.name}" is already active.'})
                messages.info(request, f'Product "{product.name}" is already active.')
            return redirect('product_detail', pk=pk)

        # Delete request (default or explicit)
        # Staff can delete active products directly; regular users must unlist first
        if product.is_active and not request.user.is_staff:
            if is_ajax:
                return JsonResponse({'success': False, 'error': 'Unlist the product first before deleting.'}, status=400)
            messages.error(request, 'Unlist the product first before deleting.')
            return redirect('product_detail', pk=pk)

        product_name = product.name
        product.delete()
        
        if is_ajax:
            return JsonResponse({'success': True, 'message': f'Product "{product_name}" has been deleted.'})
        
        messages.success(request, f'Product "{product_name}" has been deleted.')
        return redirect('my_products')
    
    context = {
        'title': f'Delete {product.name} - AgriLink',
        'product': product
    }
    return render(request, 'products/product_confirm_delete.html', context)


@login_required
def my_products(request):
    """
    Display farmer's own products (FR-9: My Products section)
    Only accessible to farmers
    """
    if not request.user.is_farmer():
        messages.error(request, 'Only farmers can access this page.')
        return redirect('product_list')
    
    # Get farmer's products with sorting
    sort_by = request.GET.get('sort', '-created_at')
    valid_sorts = ['-created_at', 'created_at', 'price', '-price', 'name', '-total_sales', 'popularity']
    if sort_by == 'popularity':
        products = request.user.products.all().order_by('-total_sales')
    elif sort_by in valid_sorts:
        products = request.user.products.all().order_by(sort_by)
    else:
        products = request.user.products.all().order_by('-created_at')
    
    # Filter by active/inactive
    status_filter = request.GET.get('status')
    if status_filter == 'active':
        products = products.filter(is_active=True)
    elif status_filter == 'inactive':
        products = products.filter(is_active=False)
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'title': 'My Products - AgriLink',
        'page_obj': page_obj,
        'sort_by': sort_by,
        'status_filter': status_filter,
        'total_products': products.count(),
        'active_products': request.user.products.filter(is_active=True).count(),
        'inactive_products': request.user.products.filter(is_active=False).count()
    }
    return render(request, 'products/my_products.html', context)


@require_POST
@login_required
def calculate_fair_price_view(request):
    """
    API endpoint for Fair Price Calculator (Feature 6.2)
    
    Accepts POST with JSON body:
        - farmgate_price: Base price at farm gate (per unit)
        - transport_cost: Total transport/logistics cost
        - quantity: Total quantity in kg
        - supermarket_price: (optional) For comparison/savings calculation
    
    Returns JSON with calculated values or error message.
    """
    import json
    
    try:
        data = json.loads(request.body)
        
        # Extract and validate inputs
        farmgate_price = data.get('farmgate_price')
        transport_cost = data.get('transport_cost', 0)
        quantity = data.get('quantity')
        supermarket_price = data.get('supermarket_price')
        
        # Validate required fields
        if farmgate_price is None or quantity is None:
            return JsonResponse({
                'success': False,
                'error': 'Farmgate price and quantity are required.'
            }, status=400)
        
        # Convert to Decimal
        try:
            farmgate_price = Decimal(str(farmgate_price))
            transport_cost = Decimal(str(transport_cost)) if transport_cost else Decimal('0')
            quantity = Decimal(str(quantity))
        except (InvalidOperation, ValueError):
            return JsonResponse({
                'success': False,
                'error': 'Invalid numeric values provided.'
            }, status=400)
        
        # Validate positive values
        if farmgate_price <= 0:
            return JsonResponse({
                'success': False,
                'error': 'Farmgate price must be greater than zero.'
            }, status=400)
        
        if quantity <= 0:
            return JsonResponse({
                'success': False,
                'error': 'Quantity must be greater than zero.'
            }, status=400)
        
        if transport_cost < 0:
            return JsonResponse({
                'success': False,
                'error': 'Transport cost cannot be negative.'
            }, status=400)
        
        # Calculate fair price
        result = calculate_fair_price(farmgate_price, transport_cost, quantity)
        
        # Calculate savings if supermarket price provided
        savings_percent = None
        if supermarket_price:
            try:
                supermarket_price = Decimal(str(supermarket_price))
                if supermarket_price > 0:
                    savings_percent = float(calculate_buyer_savings(
                        result['fair_price'], 
                        supermarket_price
                    ))
            except (InvalidOperation, ValueError):
                pass  # Ignore invalid supermarket price
        
        return JsonResponse({
            'success': True,
            'fair_price': float(result['fair_price']),
            'unit_logistics': float(result['unit_logistics']),
            'base_cost': float(result['base_cost']),
            'profit_margin': float(result['profit_margin']),
            'farmgate_price': float(result['farmgate_price']),
            'savings_percent': savings_percent
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON data.'
        }, status=400)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': 'An error occurred while calculating the price.'
        }, status=500)


@login_required
def fair_price_view(request):
    """
    Fair Price Calculator page (Feature 6.2)
    Market Split Model: Fair Price = (Farmgate + Market) / 2
    Fallback: Farmgate * 1.35 if no market price
    
    GET: Render calculator page with user's calculation history
    POST: Save a new calculation to the database
    """
    import json
    
    if not request.user.is_farmer():
        messages.error(request, 'The calculator is available to farmers only.')
        return redirect('product_list')
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            # Extract fields
            # Accept both the existing crop_name key and the new product_name key
            crop_name = (data.get('product_name') or data.get('crop_name') or '').strip()
            farmgate_price = data.get('farmgate_price')
            market_price = data.get('market_price')  # Optional
            fair_price = data.get('fair_price')
            category = (data.get('category') or '').strip()
            
            # Validate crop name
            if not crop_name:
                return JsonResponse({
                    'success': False,
                    'error': 'Please enter a product name.'
                }, status=400)
            
            # Validate numeric fields
            try:
                farmgate_price = Decimal(str(farmgate_price))
                market_price = Decimal(str(market_price)) if market_price else None
                fair_price = Decimal(str(fair_price))
            except (InvalidOperation, ValueError, TypeError):
                return JsonResponse({
                    'success': False,
                    'error': 'Invalid numeric values provided.'
                }, status=400)
            
            # Create the saved calculation
            calculation = SavedCalculation.objects.create(
                user=request.user,
                crop_name=crop_name,
                category=category,
                farmgate_price=farmgate_price,
                market_price=market_price,
                fair_price=fair_price
            )
            
            return JsonResponse({
                'success': True,
                'message': 'Calculation saved successfully!',
                'id': calculation.id
            })
            
        except json.JSONDecodeError:
            return JsonResponse({
                'success': False,
                'error': 'Invalid JSON data.'
            }, status=400)
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': 'An error occurred while saving.'
            }, status=500)
    
    # GET request - render calculator page
    # Limit fields to avoid loading any corrupted numeric values (defensive)
    history_qs = SavedCalculation.objects.filter(user=request.user).only(
        'id', 'crop_name', 'category', 'fair_price', 'created_at'
    )[:5]
    
    # Defensive: skip any rows that still fail conversion
    history = []
    for calc in history_qs:
        try:
            _ = calc.fair_price + Decimal('0')
            history.append(calc)
        except (InvalidOperation, TypeError):
            continue

    categories = Category.objects.annotate(
        sort_priority=Case(
            When(name='Others', then=Value(1)),
            default=Value(0),
            output_field=IntegerField()
        )
    ).order_by('sort_priority', 'name')
    
    context = {
        'title': 'Fair Price Calculator - AgriLink',
        'history': history,
        'categories': categories
    }
    return render(request, 'products/calculator.html', context)


@login_required
@require_POST
def delete_saved_calculation(request, calc_id):
    """
    Delete a saved fair price calculation for the current user
    """
    calculation = get_object_or_404(SavedCalculation, id=calc_id, user=request.user)
    calculation.delete()
    return JsonResponse({'success': True})
