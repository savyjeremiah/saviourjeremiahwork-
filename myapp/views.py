from django.shortcuts import render, redirect, get_object_or_404
from .models import Product, Category, Cart, CartItem, Wishlist, ShippingAddress
from django.contrib import messages
from django.contrib.auth import login as auth_login, authenticate, logout
from .forms import RegistrationForm, SearchForm, WishlistForm, ShippingAddressForm
from django.urls import reverse
from django.conf import settings
import uuid
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from paypal.standard.ipn.signals import valid_ipn_received
from django.dispatch import receiver
from paypal.standard.forms import PayPalPaymentsForm


def home(request):
    products = Product.objects.all()
    return render(request, 'home.html', {"products": products})

def about(request):
    return render(request, 'about.html')

def product_detail(request, pk):
    product = get_object_or_404(Product, pk=pk)
    return render(request, 'product_page.html', {'product': product})

def category_view(request, food):
    food = food.replace('-', ' ')
    try:
        category = Category.objects.get(name=food)
        products = Product.objects.filter(category=category)
        return render(request, 'category.html', {'category': category, 'products': products})
    except Category.DoesNotExist:
        messages.error(request, 'That category does not exist.')
        return redirect('home')

def cart_view(request):
    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key
        cart, _ = Cart.objects.get_or_create(user=None, session_key=session_key)
    
    items = cart.items.all()
    total_price = sum(item.get_total_price() for item in items)
    return render(request, 'cart.html', {
        'cart': cart,
        'items': items,
        'total_price': total_price,
    })

def add_to_cart(request, product_id):
    if not request.user.is_authenticated:
        return redirect('login')

    product = get_object_or_404(Product, id=product_id)
    cart, _ = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)

    if not created:
        cart_item.quantity += 1
        cart_item.save()

    return redirect('cart_view')

def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    cart_item.delete()
    return redirect('cart_view')

def update_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id)
    quantity = int(request.POST.get('quantity', 1))
    if quantity > 0:
        cart_item.quantity = quantity
        cart_item.save()
    return redirect('cart_view')

def register(request):
    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            return redirect('home')
        else:
            messages.error(request, "There was an error with your registration.")
    else:
        form = RegistrationForm()
    return render(request, 'register.html', {'form': form})

def login(request):
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('home')
        else:
            return render(request, 'login.html', {'error': 'Invalid credentials'})
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('home')

def search_view(request):
    form = SearchForm()
    results = []
    query = None

    if 'query' in request.GET:
        form = SearchForm(request.GET)
        if form.is_valid():
            query = form.cleaned_data['query']
            results = Product.objects.filter(name__icontains(query))

    return render(request, 'search.html', {'form': form, 'query': query, 'results': results})

def add_shipping_address(request):
    if request.method == 'POST':
        form = ShippingAddressForm(request.POST)
        if form.is_valid():
            shipping_address = form.save(commit=False)
            shipping_address.user = request.user
            shipping_address.save()
            return redirect('shipping_address_list')
    else:
        form = ShippingAddressForm()

    return render(request, 'add_shipping_address.html', {'form': form})

def shipping_address_list(request):
    addresses = ShippingAddress.objects.filter(user=request.user)
    return render(request, 'shipping_address_list.html', {'addresses': addresses})

def wishlist_view(request):
    wishlist, created = Wishlist.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = WishlistForm(request.POST, instance=wishlist)
        if form.is_valid():
            form.save()
            return redirect('wishlist')
    else:
        form = WishlistForm(instance=wishlist)
    return render(request, 'wishlist.html', {'form': form, 'wishlist': wishlist})

def remove_from_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist = Wishlist.objects.get(user=request.user)
    wishlist.products.remove(product)
    return redirect('wishlist')

@csrf_exempt
def paypal_ipn(request):
    return HttpResponse("PayPal IPN endpoint")

@receiver(valid_ipn_received)
def payment_notification(sender, **kwargs):
    ipn_obj = sender
    if ipn_obj.payment_status == 'Completed':
        if ipn_obj.receiver_email != settings.PAYPAL_RECEIVER_EMAIL:
            return
        try:
            cart = Cart.objects.get(user=request.user)
            cart.is_paid = True
            cart.save()
        except Cart.DoesNotExist:
            pass

def payment_success(request):
    return render(request, 'payment_success.html')

def payment_failed(request):
    return render(request, 'payment_failed.html')



def checkout(request, product_id):

    product = Product.objects.get(id=product_id)

    host = request.get_host()

    paypal_checkout = {
        'business': settings.PAYPAL_RECEIVER_EMAIL,
        'amount': product.price,
        'item_name': product.name,
        'invoice': uuid.uuid4(),
        'currency_code': 'USD',
        'notify_url': f"http://{host}{reverse('paypal-ipn')}",
        'return_url': f"http://{host}{reverse('payment-success', kwargs = {'product_id': product.id})}",
        'cancel_url': f"http://{host}{reverse('payment-failed', kwargs = {'product_id': product.id})}",
    }

    paypal_payment = PayPalPaymentsForm(initial=paypal_checkout)

    context = {
        'product': product,
        'paypal': paypal_payment
    }

    return render(request, 'checkout.html', context)

