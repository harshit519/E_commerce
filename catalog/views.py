from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.paginator import Paginator
from .models import Product, Category, Cart, CartItem, Order, OrderItem
from .forms import UserRegistrationForm, CheckoutForm, ProductSearchForm, CartItemForm, ContactForm

def home(request):
    """Home page with featured products and categories"""
    featured_products = Product.objects.filter(is_active=True)[:6]
    categories = Category.objects.all()[:6]
    
    context = {
        'featured_products': featured_products,
        'categories': categories,
    }
    return render(request, 'catalog/home.html', context)

def product_list(request):
    """Product listing page with search and filtering"""
    products = Product.objects.filter(is_active=True)
    search_form = ProductSearchForm(request.GET)
    
    if search_form.is_valid():
        search_query = search_form.cleaned_data.get('search_query')
        category = search_form.cleaned_data.get('category')
        min_price = search_form.cleaned_data.get('min_price')
        max_price = search_form.cleaned_data.get('max_price')
        
        if search_query:
            products = products.filter(
                Q(name__icontains=search_query) | 
                Q(description__icontains=search_query)
            )
        
        if category:
            products = products.filter(category__name=category)
        
        if min_price:
            products = products.filter(price__gte=min_price)
        
        if max_price:
            products = products.filter(price__lte=max_price)
    
    # Pagination
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_form': search_form,
        'categories': Category.objects.all(),
    }
    return render(request, 'catalog/product_list.html', context)

def product_detail(request, product_id):
    """Product detail page"""
    product = get_object_or_404(Product, id=product_id, is_active=True)
    related_products = Product.objects.filter(
        category=product.category, 
        is_active=True
    ).exclude(id=product.id)[:4]
    
    cart_form = CartItemForm()
    
    context = {
        'product': product,
        'related_products': related_products,
        'cart_form': cart_form,
    }
    return render(request, 'catalog/product_detail.html', context)

def category_products(request, category_id):
    """Products filtered by category"""
    category = get_object_or_404(Category, id=category_id)
    products = Product.objects.filter(category=category, is_active=True)
    
    paginator = Paginator(products, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'category': category,
        'page_obj': page_obj,
    }
    return render(request, 'catalog/category_products.html', context)

def register(request):
    """User registration"""
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, 'Account created successfully! Please log in.')
            return redirect('catalog:login')
    else:
        form = UserRegistrationForm()
    
    return render(request, 'catalog/register.html', {'form': form})

def user_login(request):
    """User login"""
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('catalog:home')
        else:
            messages.error(request, 'Invalid username or password.')
    
    return render(request, 'catalog/login.html')

@login_required
def add_to_cart(request, product_id):
    """Add product to cart"""
    if request.method == 'POST':
        product = get_object_or_404(Product, id=product_id, is_active=True)
        form = CartItemForm(request.POST)
        
        if form.is_valid():
            quantity = form.cleaned_data['quantity']
            
            # Get or create cart for user
            cart, created = Cart.objects.get_or_create(user=request.user)
            
            # Check if product already in cart
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart, 
                product=product,
                defaults={'quantity': quantity}
            )
            
            if not created:
                cart_item.quantity += quantity
                cart_item.save()
            
            messages.success(request, f'{product.name} added to cart!')
            return redirect('catalog:cart')
    
    return redirect('catalog:product_detail', product_id=product_id)

@login_required
def cart_view(request):
    """View shopping cart"""
    try:
        cart = Cart.objects.get(user=request.user)
        cart_items = cart.items.all()
    except Cart.DoesNotExist:
        cart = None
        cart_items = []
    
    context = {
        'cart': cart,
        'cart_items': cart_items,
    }
    return render(request, 'catalog/cart.html', context)

@login_required
@require_POST
def update_cart_item(request, item_id):
    """Update cart item quantity"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    quantity = int(request.POST.get('quantity', 1))
    
    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
        messages.success(request, 'Cart updated successfully!')
    else:
        cart_item.delete()
        messages.success(request, 'Item removed from cart!')
    
    return redirect('catalog:cart')

@login_required
@require_POST
def remove_from_cart(request, item_id):
    """Remove item from cart"""
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    product_name = cart_item.product.name
    cart_item.delete()
    messages.success(request, f'{product_name} removed from cart!')
    return redirect('catalog:cart')

@login_required
def checkout(request):
    """Checkout process"""
    try:
        cart = Cart.objects.get(user=request.user)
        if not cart.items.exists():
            messages.warning(request, 'Your cart is empty!')
            return redirect('catalog:cart')
    except Cart.DoesNotExist:
        messages.warning(request, 'Your cart is empty!')
        return redirect('catalog:cart')
    
    if request.method == 'POST':
        form = CheckoutForm(request.POST)
        if form.is_valid():
            # Create order
            order = form.save(commit=False)
            order.user = request.user
            order.total_amount = cart.total_price
            order.save()
            
            # Create order items
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    product_name=cart_item.product.name,
                    price=cart_item.product.price,
                    quantity=cart_item.quantity
                )
                
                # Update product stock
                product = cart_item.product
                product.stock -= cart_item.quantity
                product.save()
            
            # Clear cart
            cart.delete()
            
            messages.success(request, f'Order placed successfully! Order number: {order.order_number}')
            return redirect('catalog:order_confirmation', order_id=order.id)
    else:
        form = CheckoutForm()
    
    context = {
        'form': form,
        'cart': cart,
    }
    return render(request, 'catalog/checkout.html', context)

@login_required
def order_confirmation(request, order_id):
    """Order confirmation page"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'catalog/order_confirmation.html', {'order': order})

@login_required
def order_history(request):
    """User's order history"""
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    
    paginator = Paginator(orders, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'catalog/order_history.html', context)

@login_required
def order_detail(request, order_id):
    """Order detail view"""
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'catalog/order_detail.html', {'order': order})

def contact(request):
    """Contact form"""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            # Here you would typically send an email
            messages.success(request, 'Thank you for your message! We will get back to you soon.')
            return redirect('catalog:contact')
    else:
        form = ContactForm()
    
    return render(request, 'catalog/contact.html', {'form': form})

def about(request):
    """About page"""
    return render(request, 'catalog/about.html')

def user_logout(request):
    """Custom logout view that handles GET requests"""
    logout(request)
    messages.success(request, 'You have been successfully logged out!')
    return redirect('catalog:home')