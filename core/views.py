from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from products.models import Product, Category, RecentlyViewed
from cart.models import Coupon
from .models import ContactMessage, NewsletterSubscriber, DeliveryPincode

def home_view(request):
    featured_categories = Category.objects.filter(is_featured=True)[:6]
    
    # Flash deals: products with is_flash_deal=True or highest discounts
    now = timezone.now()
    flash_deals = Product.objects.filter(
        is_active=True,
        is_flash_deal=True,
        stock__gt=0
    )[:6]
    if not flash_deals.exists():
        # Fallback to products with discount_price
        flash_deals = Product.objects.filter(
            is_active=True,
            discount_price__isnull=False,
            stock__gt=0
        ).order_by('-price')[:6]

    trending_products = Product.objects.filter(
        is_active=True,
        stock__gt=0
    ).order_by('-average_rating', '-review_count')[:8]

    bestsellers = Product.objects.filter(
        is_active=True,
        is_bestseller=True,
        stock__gt=0
    )[:8]

    new_arrivals = Product.objects.filter(
        is_active=True,
        stock__gt=0
    ).order_by('-created_at')[:8]

    # Recently viewed
    recently_viewed_products = []
    if request.user.is_authenticated:
        rv_items = RecentlyViewed.objects.filter(user=request.user).select_related('product')[:6]
        recently_viewed_products = [item.product for item in rv_items if item.product.is_active]
    elif request.session.session_key:
        rv_items = RecentlyViewed.objects.filter(session_key=request.session.session_key).select_related('product')[:6]
        recently_viewed_products = [item.product for item in rv_items if item.product.is_active]

    # Recommended for user
    recommended = Product.objects.filter(
        is_active=True,
        is_featured=True,
        stock__gt=0
    )[:8]

    active_coupons = Coupon.objects.filter(is_active=True, valid_to__gte=now)[:3]

    context = {
        'featured_categories': featured_categories,
        'flash_deals': flash_deals,
        'trending_products': trending_products,
        'bestsellers': bestsellers,
        'new_arrivals': new_arrivals,
        'recently_viewed': recently_viewed_products,
        'recommended': recommended,
        'active_coupons': active_coupons,
    }
    return render(request, 'core/home.html', context)


def deals_view(request):
    now = timezone.now()
    flash_deals = Product.objects.filter(
        is_active=True,
        discount_price__isnull=False,
        stock__gt=0
    ).order_by('-price')

    active_coupons = Coupon.objects.filter(is_active=True, valid_to__gte=now)

    context = {
        'flash_deals': flash_deals,
        'active_coupons': active_coupons,
    }
    return render(request, 'core/deals.html', context)


def about_view(request):
    return render(request, 'core/about.html')


def contact_view(request):
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        message = request.POST.get('message', '').strip()

        if name and email and message:
            ContactMessage.objects.create(
                name=name,
                email=email,
                subject=subject or 'General Inquiry',
                message=message
            )
            messages.success(request, "Thank you for reaching out! Our support team will get back to you within 24 hours.")
            return redirect('core:contact')
        else:
            messages.error(request, "Please fill in all required fields.")

    return render(request, 'core/contact.html')


def privacy_view(request):
    return render(request, 'core/privacy.html')


def terms_view(request):
    return render(request, 'core/terms.html')


def check_pincode_api(request):
    pincode = request.GET.get('pincode', '').strip()
    if not pincode or len(pincode) != 6 or not pincode.isdigit():
        return JsonResponse({
            'serviceable': False,
            'message': 'Please enter a valid 6-digit Indian PIN code.'
        })

    entry = DeliveryPincode.objects.filter(pincode=pincode).first()
    if entry:
        if entry.is_serviceable:
            return JsonResponse({
                'serviceable': True,
                'city': entry.city,
                'state': entry.state,
                'days': entry.estimated_days,
                'cod': entry.cod_available,
                'message': f"Delivery available to {entry.city}, {entry.state} in {entry.estimated_days} business days."
            })
        else:
            return JsonResponse({
                'serviceable': False,
                'message': f"Delivery is currently unserviceable to {pincode}."
            })
    else:
        # Default fallback for unlisted PIN codes (standard 4-6 business days)
        return JsonResponse({
            'serviceable': True,
            'city': 'Standard Zone',
            'state': '',
            'days': 5,
            'cod': True,
            'message': f"Delivery available to PIN {pincode} in approximately 4-5 business days."
        })


def newsletter_subscribe_api(request):
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if email and '@' in email:
            sub, created = NewsletterSubscriber.objects.get_or_create(email=email)
            if created:
                msg = "You have successfully subscribed to the THE ULTIMATE SHOPPING newsletter! Exclusive deals will arrive in your inbox."
            else:
                msg = "You are already subscribed to our newsletter!"
            return JsonResponse({'success': True, 'message': msg})
        return JsonResponse({'success': False, 'message': 'Please provide a valid email address.'})
    return JsonResponse({'success': False, 'message': 'Invalid request.'})
