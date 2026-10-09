from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.http import JsonResponse
from .models import UserProfile, Address, LoyaltyTransaction
from .forms import RegisterForm, LoginForm, ProfileForm, AddressForm
from products.models import PriceAlert
from orders.models import Order
from cart.utils import merge_guest_cart

def register_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    if request.method == 'POST':
        form = RegisterForm(request.POST)
        if form.is_valid():
            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )
            name_parts = form.cleaned_data['full_name'].split(' ', 1)
            user.first_name = name_parts[0]
            if len(name_parts) > 1:
                user.last_name = name_parts[1]
            user.save()

            # Profile already created by signal, update phone and add welcome loyalty transaction
            profile = user.profile
            profile.phone = form.cleaned_data.get('phone', '')
            profile.save()

            LoyaltyTransaction.objects.create(
                user=user,
                points=100,
                description="Welcome Bonus: 100 Reward Points for joining THE ULTIMATE SHOPPING!"
            )

            # Log user in
            login(request, user)
            merge_guest_cart(request, user)

            messages.success(request, f"Welcome to THE ULTIMATE SHOPPING, {user.first_name or user.username}! You received 100 bonus reward points.")
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('core:home')
        else:
            messages.error(request, "Please correct the errors in the registration form.")
    else:
        form = RegisterForm()

    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')

    next_url = request.GET.get('next', '')
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username_or_email = form.cleaned_data['username_or_email']
            password = form.cleaned_data['password']

            # Check if email was provided instead of username
            user_obj = None
            if '@' in username_or_email:
                user_obj = User.objects.filter(email__iexact=username_or_email).first()
                if user_obj:
                    user_obj = authenticate(request, username=user_obj.username, password=password)
            else:
                user_obj = authenticate(request, username=username_or_email, password=password)

            if user_obj is not None:
                login(request, user_obj)
                merge_guest_cart(request, user_obj)
                messages.success(request, f"Welcome back, {user_obj.first_name or user_obj.username}!")
                
                target = request.POST.get('next') or request.GET.get('next') or 'core:home'
                return redirect(target)
            else:
                messages.error(request, "Invalid username/email or password.")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form, 'next': next_url})


def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out securely. See you again soon!")
    return redirect('core:home')


@login_required
def account_dashboard(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    recent_orders = Order.objects.filter(user=request.user).order_by('-created_at')[:5]
    addresses = Address.objects.filter(user=request.user)
    price_alerts = PriceAlert.objects.filter(user=request.user).select_related('product')[:5]
    loyalty_transactions = LoyaltyTransaction.objects.filter(user=request.user).order_by('-created_at')[:5]

    context = {
        'profile': profile,
        'recent_orders': recent_orders,
        'addresses': addresses,
        'price_alerts': price_alerts,
        'loyalty_transactions': loyalty_transactions,
    }
    return render(request, 'accounts/account.html', context)


@login_required
def profile_update(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=request.user, profile=profile)
        if form.is_valid():
            form.save()
            profile.phone = form.cleaned_data.get('phone', '')
            profile.save()
            messages.success(request, "Your profile information was updated successfully.")
            return redirect('accounts:dashboard')
    else:
        form = ProfileForm(instance=request.user, profile=profile)

    return render(request, 'accounts/profile_edit.html', {'form': form, 'profile': profile})


@login_required
def addresses_list(request):
    addresses = Address.objects.filter(user=request.user)
    form = AddressForm()
    return render(request, 'accounts/addresses.html', {'addresses': addresses, 'form': form})


@login_required
def address_create(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid():
            address = form.save(commit=False)
            address.user = request.user
            # If this is the user's first address, make it default
            if not Address.objects.filter(user=request.user).exists():
                address.is_default = True
            address.save()
            messages.success(request, "New address added successfully.")
            next_url = request.POST.get('next') or request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('accounts:addresses')
        else:
            messages.error(request, "Failed to save address. Please check input fields.")
    return redirect('accounts:addresses')


@login_required
def address_edit(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request, "Address updated successfully.")
            return redirect('accounts:addresses')
    else:
        form = AddressForm(instance=address)
    return render(request, 'accounts/address_edit.html', {'form': form, 'address': address})


@login_required
def address_delete(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    if request.method == 'POST':
        address.delete()
        messages.success(request, "Address removed successfully.")
    return redirect('accounts:addresses')


@login_required
def address_set_default(request, pk):
    address = get_object_or_404(Address, pk=pk, user=request.user)
    address.is_default = True
    address.save()
    messages.success(request, f"'{address.full_name}' address set as your default shipping address.")
    return redirect('accounts:addresses')


@login_required
def price_alerts_list(request):
    alerts = PriceAlert.objects.filter(user=request.user).select_related('product')
    return render(request, 'accounts/price_alerts.html', {'alerts': alerts})


@login_required
def price_alert_delete(request, pk):
    alert = get_object_or_404(PriceAlert, pk=pk, user=request.user)
    if request.method == 'POST':
        product_name = alert.product.name
        alert.delete()
        messages.success(request, f"Price alert for '{product_name}' was removed.")
    return redirect('accounts:price_alerts')


@login_required
def loyalty_history(request):
    profile, _ = UserProfile.objects.get_or_create(user=request.user)
    transactions = LoyaltyTransaction.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'accounts/loyalty.html', {'profile': profile, 'transactions': transactions})
