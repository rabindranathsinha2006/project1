from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator
from django.db.models import Q, Avg, Count
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from decimal import Decimal
from .models import (
    Product, Category, Review, Wishlist,
    PriceAlert, RestockSubscription, RecentlyViewed
)

def product_list_view(request):
    queryset = Product.objects.filter(is_active=True).select_related('category')

    # Search filter
    q = request.GET.get('q', '').strip()
    if q:
        queryset = queryset.filter(
            Q(name__icontains=q) |
            Q(description__icontains=q) |
            Q(brand__icontains=q) |
            Q(category__name__icontains=q)
        )

    # Category filter
    category_slug = request.GET.get('category', '').strip()
    current_category = None
    if category_slug:
        current_category = get_object_or_404(Category, slug=category_slug)
        queryset = queryset.filter(category=current_category)

    # Brand filter
    brand = request.GET.get('brand', '').strip()
    if brand:
        queryset = queryset.filter(brand__iexact=brand)

    # Price range
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    if min_price:
        try:
            queryset = queryset.filter(price__gte=Decimal(min_price))
        except (ValueError, TypeError):
            pass
    if max_price:
        try:
            queryset = queryset.filter(price__lte=Decimal(max_price))
        except (ValueError, TypeError):
            pass

    # Rating filter
    min_rating = request.GET.get('rating')
    if min_rating:
        try:
            queryset = queryset.filter(average_rating__gte=Decimal(min_rating))
        except (ValueError, TypeError):
            pass

    # Stock availability
    in_stock = request.GET.get('in_stock')
    if in_stock == '1':
        queryset = queryset.filter(stock__gt=0)

    # Sorting
    sort = request.GET.get('sort', 'newest')
    if sort == 'price_low':
        queryset = queryset.order_by('price')
    elif sort == 'price_high':
        queryset = queryset.order_by('-price')
    elif sort == 'rating':
        queryset = queryset.order_by('-average_rating', '-review_count')
    elif sort == 'popularity':
        queryset = queryset.order_by('-is_bestseller', '-review_count')
    else:  # newest
        queryset = queryset.order_by('-created_at')

    # Available brands and categories for filter sidebar
    all_categories = Category.objects.all()
    all_brands = Product.objects.filter(is_active=True).values_list('brand', flat=True).distinct()

    # Pagination
    paginator = Paginator(queryset, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Query params string for preserving pagination with filters
    query_params = request.GET.copy()
    if 'page' in query_params:
        del query_params['page']
    query_string = query_params.urlencode()

    context = {
        'page_obj': page_obj,
        'products': page_obj.object_list,
        'total_count': paginator.count,
        'categories': all_categories,
        'brands': sorted(list(set(b for b in all_brands if b))),
        'current_category': current_category,
        'search_query': q,
        'current_sort': sort,
        'min_price': min_price or '',
        'max_price': max_price or '',
        'current_rating': min_rating or '',
        'in_stock': in_stock or '',
        'selected_brand': brand,
        'query_string': query_string,
    }
    return render(request, 'products/product_list.html', context)


def category_detail_view(request, slug):
    category = get_object_or_404(Category, slug=slug)
    # Redirect to product list with category filter parameter
    return redirect(f"/products/?category={category.slug}")


def product_detail_view(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    images = product.images.all()

    # Record recently viewed
    if request.user.is_authenticated:
        RecentlyViewed.objects.update_or_create(
            user=request.user,
            product=product
        )
    else:
        if not request.session.session_key:
            request.session.save()
        RecentlyViewed.objects.update_or_create(
            session_key=request.session.session_key,
            product=product
        )

    # Reviews and stats
    reviews = product.reviews.filter(is_approved=True).select_related('user')
    rating_breakdown = {}
    total_reviews = reviews.count()
    for star in range(1, 6):
        count = reviews.filter(rating=star).count()
        pct = int((count / total_reviews * 100)) if total_reviews > 0 else 0
        rating_breakdown[star] = {'count': count, 'percent': pct}

    # Related products
    related_products = Product.objects.filter(
        category=product.category,
        is_active=True
    ).exclude(id=product.id)[:4]

    # Recommended products (e.g. bestsellers or highest rated in general)
    recommended_products = Product.objects.filter(
        is_active=True
    ).exclude(id=product.id).order_by('-average_rating', '-is_bestseller')[:4]

    # Check if user has saved this in wishlist or set price alert
    in_wishlist = False
    user_price_alert = None
    user_review = None
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()
        user_price_alert = PriceAlert.objects.filter(user=request.user, product=product).first()
        user_review = Review.objects.filter(user=request.user, product=product).first()
    else:
        guest_wishlist = request.session.get('guest_wishlist', [])
        in_wishlist = product.id in guest_wishlist

    # Compare check
    compare_list = request.session.get('compare_list', [])
    in_compare = product.id in compare_list

    context = {
        'product': product,
        'images': images,
        'reviews': reviews[:10],
        'total_reviews': total_reviews,
        'rating_breakdown': rating_breakdown,
        'related_products': related_products,
        'recommended_products': recommended_products,
        'in_wishlist': in_wishlist,
        'in_compare': in_compare,
        'user_price_alert': user_price_alert,
        'user_review': user_review,
    }
    return render(request, 'products/product_detail.html', context)


def product_reviews_view(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    reviews = product.reviews.filter(is_approved=True).select_related('user')

    rating_breakdown = {}
    total_reviews = reviews.count()
    for star in range(1, 6):
        count = reviews.filter(rating=star).count()
        pct = int((count / total_reviews * 100)) if total_reviews > 0 else 0
        rating_breakdown[star] = {'count': count, 'percent': pct}

    context = {
        'product': product,
        'reviews': reviews,
        'total_reviews': total_reviews,
        'rating_breakdown': rating_breakdown,
    }
    return render(request, 'products/product_reviews.html', context)


@login_required
def add_review_view(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    if request.method == 'POST':
        rating = request.POST.get('rating')
        headline = request.POST.get('headline', '').strip()
        comment = request.POST.get('comment', '').strip()

        if not rating or not comment:
            messages.error(request, "Please provide both a star rating and your review comments.")
            return redirect('products:detail', slug=slug)

        try:
            rating_val = int(rating)
            if rating_val < 1 or rating_val > 5:
                raise ValueError
        except ValueError:
            messages.error(request, "Invalid rating value.")
            return redirect('products:detail', slug=slug)

        # Check if verified purchaser (bought this product in an order)
        has_purchased = request.user.orders.filter(
            items__product=product,
            status__in=['delivered', 'shipped', 'confirmed']
        ).exists()

        review, created = Review.objects.update_or_create(
            product=product,
            user=request.user,
            defaults={
                'rating': rating_val,
                'headline': headline or f"Rating {rating_val}/5",
                'comment': comment,
                'is_verified_purchase': has_purchased,
                'is_approved': True,
            }
        )

        product.update_rating_stats()
        action_word = "submitted" if created else "updated"
        messages.success(request, f"Thank you! Your review for {product.name} has been {action_word}.")

    return redirect('products:detail', slug=slug)


def wishlist_view(request):
    if request.user.is_authenticated:
        items = Wishlist.objects.filter(user=request.user).select_related('product')
        products = [item.product for item in items]
    else:
        guest_ids = request.session.get('guest_wishlist', [])
        products = Product.objects.filter(id__in=guest_ids, is_active=True)

    return render(request, 'products/wishlist.html', {'products': products})


def toggle_wishlist_view(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    in_wishlist = False

    if request.user.is_authenticated:
        item = Wishlist.objects.filter(user=request.user, product=product).first()
        if item:
            item.delete()
            in_wishlist = False
            msg = f"{product.name} removed from your wishlist."
        else:
            Wishlist.objects.create(user=request.user, product=product)
            in_wishlist = True
            msg = f"{product.name} added to your wishlist!"
        count = Wishlist.objects.filter(user=request.user).count()
    else:
        guest_wishlist = request.session.get('guest_wishlist', [])
        if product.id in guest_wishlist:
            guest_wishlist.remove(product.id)
            in_wishlist = False
            msg = f"{product.name} removed from your wishlist."
        else:
            guest_wishlist.append(product.id)
            in_wishlist = True
            msg = f"{product.name} added to your wishlist!"
        request.session['guest_wishlist'] = guest_wishlist
        count = len(guest_wishlist)

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
        return JsonResponse({
            'success': True,
            'in_wishlist': in_wishlist,
            'count': count,
            'message': msg
        })

    messages.info(request, msg)
    referer = request.META.get('HTTP_REFERER')
    return redirect(referer or 'products:wishlist')


def compare_view(request):
    compare_ids = request.session.get('compare_list', [])
    products = Product.objects.filter(id__in=compare_ids, is_active=True).select_related('category')

    # Collect all unique specification keys across compared products
    spec_keys = set()
    for p in products:
        if isinstance(p.specifications, dict):
            spec_keys.update(p.specifications.keys())

    context = {
        'products': products,
        'spec_keys': sorted(list(spec_keys)),
    }
    return render(request, 'products/compare.html', context)


def toggle_compare_view(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    compare_list = request.session.get('compare_list', [])
    in_compare = False

    if product.id in compare_list:
        compare_list.remove(product.id)
        msg = f"{product.name} removed from comparison."
        in_compare = False
    else:
        if len(compare_list) >= 4:
            msg = "You can compare at most 4 products at a time. Please remove one first."
            if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
                return JsonResponse({'success': False, 'message': msg, 'count': len(compare_list)})
            messages.warning(request, msg)
            return redirect(request.META.get('HTTP_REFERER', 'products:compare'))

        compare_list.append(product.id)
        msg = f"{product.name} added to comparison!"
        in_compare = True

    request.session['compare_list'] = compare_list

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
        return JsonResponse({
            'success': True,
            'in_compare': in_compare,
            'count': len(compare_list),
            'message': msg
        })

    messages.info(request, msg)
    referer = request.META.get('HTTP_REFERER')
    return redirect(referer or 'products:compare')


def clear_compare_view(request):
    request.session['compare_list'] = []
    messages.info(request, "Comparison list cleared.")
    return redirect('products:compare')


@login_required
def set_price_alert_view(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    if request.method == 'POST':
        target_price = request.POST.get('target_price')
        try:
            target = Decimal(target_price)
            if target <= Decimal('0.00'):
                raise ValueError
            
            alert, created = PriceAlert.objects.update_or_create(
                user=request.user,
                product=product,
                defaults={'target_price': target, 'is_triggered': False}
            )
            msg = f"Price alert set! We will notify you when {product.name} drops to ₹{target}."
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': msg})
            messages.success(request, msg)
        except (ValueError, TypeError):
            msg = "Please enter a valid target price."
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': msg})
            messages.error(request, msg)

    return redirect('products:detail', slug=product.slug)


def restock_subscription_view(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        if not email and request.user.is_authenticated:
            email = request.user.email

        if email:
            RestockSubscription.objects.get_or_create(
                product=product,
                email=email,
                defaults={'user': request.user if request.user.is_authenticated else None}
            )
            msg = f"Thank you! We will notify you at {email} as soon as {product.name} is restocked."
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': True, 'message': msg})
            messages.success(request, msg)
        else:
            msg = "Please provide a valid email address."
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'message': msg})
            messages.error(request, msg)

    return redirect('products:detail', slug=product.slug)
