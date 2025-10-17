from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Product, Category
from .forms import ProductForm


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
    valid_sorts = ['-created_at', 'created_at', 'price', '-price', 'name']
    if sort_by in valid_sorts:
        products = products.order_by(sort_by)
    
    # Use paginator's count method for better performance
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    total_results = paginator.count

    # Get all categories for filter sidebar (cached)
    categories = Category.objects.all()

    context = {
        'title': 'Browse Products - AgriLink',
        'page_obj': page_obj,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
        'total_results': total_results
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

    context = {
        'title': f'{product.name} - AgriLink',
        'product': product,
        'other_products': other_products,
        'farmer_active_products_count': farmer_active_products_count
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
    
    context = {
        'title': 'Add New Product - AgriLink',
        'form': form,
        'action': 'Add'
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
    
    context = {
        'title': f'Edit {product.name} - AgriLink',
        'form': form,
        'product': product,
        'action': 'Edit'
    }
    return render(request, 'products/product_form.html', context)


@login_required
def product_delete(request, pk):
    """
    Soft delete product (set is_active=False)
    Implements FR-7 (delete product listing)
    Only product owner or admin can delete
    """
    product = get_object_or_404(Product, pk=pk)
    
    # Check permissions
    if product.farmer != request.user and not request.user.is_staff:
        messages.error(request, 'You do not have permission to delete this product.')
        return redirect('product_detail', pk=pk)
    
    if request.method == 'POST':
        product.is_active = False
        product.save()
        messages.success(request, f'Product "{product.name}" has been removed.')
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
    valid_sorts = ['-created_at', 'created_at', 'price', '-price', 'name', '-total_sales']
    if sort_by in valid_sorts:
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
