from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Sum, Count, Avg, F, Q
from django.utils import timezone
from django.utils.text import slugify
from decimal import Decimal
import json

from products.models import Product, Category, ProductImage, Review
from orders.models import Order, OrderItem, OrderTracking
from cart.models import Coupon
from accounts.models import UserProfile

def is_admin(user):
    return user.is_authenticated and (user.is_staff or user.is_superuser)

admin_required = user_passes_test(is_admin, login_url='/login/')


@admin_required
def dashboard_view(request):
    # Total sales from active orders (not cancelled)
    sales_data = Order.objects.exclude(status='cancelled').aggregate(
        total_sales=Sum('total_amount'),
        avg_order=Avg('total_amount')
    )
    total_sales = sales_data['total_sales'] or Decimal('0.00')
    avg_order_value = sales_data['avg_order'] or Decimal('0.00')

    total_orders = Order.objects.count()
    total_customers = User.objects.filter(is_staff=False).count()
    low_stock_count = Product.objects.filter(is_active=True, stock__lte=F('stock_threshold')).count()

    recent_orders = Order.objects.select_related('user').order_by('-created_at')[:8]

    # Best sellers
    best_sellers = Product.objects.filter(is_active=True).order_by('-review_count', '-is_bestseller')[:5]

    # Category breakdown
    category_stats = Category.objects.annotate(
        product_count=Count('products')
    ).order_by('-product_count')[:6]

    context = {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'total_customers': total_customers,
        'avg_order_value': avg_order_value,
        'low_stock_count': low_stock_count,
        'recent_orders': recent_orders,
        'best_sellers': best_sellers,
        'category_stats': category_stats,
    }
    return render(request, 'portal/dashboard.html', context)


@admin_required
def products_list_view(request):
    products = Product.objects.select_related('category').order_by('-created_at')
    q = request.GET.get('q', '').strip()
    if q:
        products = products.filter(Q(name__icontains=q) | Q(sku__icontains=q) | Q(brand__icontains=q))

    cat_id = request.GET.get('category')
    if cat_id:
        products = products.filter(category_id=cat_id)

    categories = Category.objects.all()
    return render(request, 'portal/products.html', {
        'products': products,
        'categories': categories,
        'q': q,
        'selected_cat': cat_id,
    })


@admin_required
def product_form_view(request, pk=None):
    product = get_object_or_404(Product, pk=pk) if pk else None
    categories = Category.objects.all()

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        category_id = request.POST.get('category')
        brand = request.POST.get('brand', 'Generic').strip()
        sku = request.POST.get('sku', '').strip()
        price = request.POST.get('price')
        discount_price = request.POST.get('discount_price') or None
        stock = request.POST.get('stock', 10)
        stock_threshold = request.POST.get('stock_threshold', 5)
        short_description = request.POST.get('short_description', '').strip()
        description = request.POST.get('description', '').strip()
        primary_image = request.POST.get('primary_image', '').strip()
        is_active = request.POST.get('is_active') == 'on'
        is_featured = request.POST.get('is_featured') == 'on'
        is_bestseller = request.POST.get('is_bestseller') == 'on'
        is_flash_deal = request.POST.get('is_flash_deal') == 'on'

        specs_str = request.POST.get('specifications', '{}')
        try:
            specs = json.loads(specs_str) if specs_str else {}
        except Exception:
            specs = {}

        if not name or not price or not sku or not category_id:
            messages.error(request, "Please fill in all required fields (Name, Category, SKU, Price).")
            return render(request, 'portal/product_form.html', {'product': product, 'categories': categories})

        category = get_object_or_404(Category, id=category_id)

        if product:
            product.name = name
            product.category = category
            product.brand = brand
            product.sku = sku
            product.price = Decimal(price)
            product.discount_price = Decimal(discount_price) if discount_price else None
            product.stock = int(stock)
            product.stock_threshold = int(stock_threshold)
            product.short_description = short_description
            product.description = description
            product.primary_image = primary_image
            product.is_active = is_active
            product.is_featured = is_featured
            product.is_bestseller = is_bestseller
            product.is_flash_deal = is_flash_deal
            product.specifications = specs
            product.save()
            messages.success(request, f"Product '{product.name}' updated successfully.")
        else:
            base_slug = slugify(name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1

            product = Product.objects.create(
                name=name,
                slug=slug,
                category=category,
                brand=brand,
                sku=sku,
                price=Decimal(price),
                discount_price=Decimal(discount_price) if discount_price else None,
                stock=int(stock),
                stock_threshold=int(stock_threshold),
                short_description=short_description,
                description=description,
                primary_image=primary_image or 'https://images.unsplash.com/photo-1523275335684-37898b6baf30?w=600',
                is_active=is_active,
                is_featured=is_featured,
                is_bestseller=is_bestseller,
                is_flash_deal=is_flash_deal,
                specifications=specs
            )
            messages.success(request, f"New product '{product.name}' created successfully.")

        return redirect('portal:products')

    return render(request, 'portal/product_form.html', {'product': product, 'categories': categories})


@admin_required
def product_delete_view(request, pk):
    product = get_object_or_404(Product, pk=pk)
    if request.method == 'POST':
        name = product.name
        product.delete()
        messages.success(request, f"Product '{name}' was deleted.")
    return redirect('portal:products')


@admin_required
def inventory_view(request):
    products = Product.objects.select_related('category').order_by('stock')
    filter_low = request.GET.get('low_only') == '1'
    if filter_low:
        products = products.filter(stock__lte=F('stock_threshold'))

    if request.method == 'POST':
        product_id = request.POST.get('product_id')
        new_stock = request.POST.get('stock')
        new_threshold = request.POST.get('stock_threshold')
        prod = get_object_or_404(Product, id=product_id)
        if new_stock is not None:
            prod.stock = int(new_stock)
        if new_threshold is not None:
            prod.stock_threshold = int(new_threshold)
        prod.save()
        messages.success(request, f"Inventory updated for {prod.name} (Stock: {prod.stock}).")
        return redirect('portal:inventory')

    return render(request, 'portal/inventory.html', {'products': products, 'low_only': filter_low})


@admin_required
def orders_list_view(request):
    orders = Order.objects.select_related('user').order_by('-created_at')
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)

    q = request.GET.get('q', '').strip()
    if q:
        orders = orders.filter(
            Q(order_number__icontains=q) |
            Q(shipping_full_name__icontains=q) |
            Q(user__username__icontains=q) |
            Q(user__email__icontains=q)
        )

    return render(request, 'portal/orders.html', {
        'orders': orders,
        'current_status': status_filter,
        'q': q,
        'status_choices': Order.STATUS_CHOICES,
    })


@admin_required
def order_detail_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        tracking_note = request.POST.get('tracking_note', '').strip()
        location = request.POST.get('location', 'Distribution Hub').strip()

        if new_status and new_status in dict(Order.STATUS_CHOICES):
            old_status = order.status
            order.status = new_status
            if new_status == 'delivered':
                order.payment_status = 'completed'
            order.save()

            title_map = {
                'placed': 'Order Placed',
                'confirmed': 'Order Confirmed',
                'packed': 'Order Packed at Warehouse',
                'shipped': 'Order Dispatched with Courier',
                'out_for_delivery': 'Out for Delivery',
                'delivered': 'Package Delivered to Customer',
                'cancelled': 'Order Cancelled by Admin',
            }

            OrderTracking.objects.create(
                order=order,
                status=new_status,
                title=title_map.get(new_status, f"Status changed to {new_status}"),
                description=tracking_note or f"Order status updated from {old_status} to {new_status}.",
                location=location
            )
            messages.success(request, f"Order #{order.order_number} status updated to '{order.get_status_display()}'.")
            return redirect('portal:order_detail', order_number=order.order_number)

    return render(request, 'portal/order_detail.html', {'order': order, 'items': order.items.all(), 'tracking_logs': order.tracking_logs.all()})


@admin_required
def analytics_view(request):
    total_sales = Order.objects.exclude(status='cancelled').aggregate(s=Sum('total_amount'))['s'] or Decimal('0.00')
    total_orders = Order.objects.count()
    completed_orders = Order.objects.filter(status='delivered').count()
    cancelled_orders = Order.objects.filter(status='cancelled').count()
    avg_order_value = Order.objects.exclude(status='cancelled').aggregate(a=Avg('total_amount'))['a'] or Decimal('0.00')

    # Top selling products
    top_items = OrderItem.objects.values('product_name').annotate(
        qty_sold=Sum('quantity'),
        total_rev=Sum('total_price')
    ).order_by('-total_rev')[:8]

    # Category performance
    categories = Category.objects.annotate(
        product_count=Count('products')
    )

    context = {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'completed_orders': completed_orders,
        'cancelled_orders': cancelled_orders,
        'avg_order_value': avg_order_value,
        'top_items': top_items,
        'categories': categories,
    }
    return render(request, 'portal/analytics.html', context)


@admin_required
def coupons_view(request):
    coupons = Coupon.objects.all().order_by('-created_at')
    if request.method == 'POST':
        code = request.POST.get('code', '').strip().upper()
        discount_type = request.POST.get('discount_type', 'percentage')
        discount_value = request.POST.get('discount_value')
        min_purchase = request.POST.get('min_purchase', '0')
        max_discount = request.POST.get('max_discount') or None
        usage_limit = request.POST.get('usage_limit', 100)

        if code and discount_value:
            valid_from = timezone.now()
            valid_to = timezone.now() + timezone.timedelta(days=365)
            Coupon.objects.create(
                code=code,
                discount_type=discount_type,
                discount_value=Decimal(discount_value),
                min_purchase=Decimal(min_purchase),
                max_discount=Decimal(max_discount) if max_discount else None,
                valid_from=valid_from,
                valid_to=valid_to,
                usage_limit=int(usage_limit),
                is_active=True
            )
            messages.success(request, f"Coupon '{code}' created successfully.")
            return redirect('portal:coupons')
        else:
            messages.error(request, "Please fill in coupon code and discount value.")

    return render(request, 'portal/coupons.html', {'coupons': coupons})


@admin_required
def toggle_coupon_status(request, pk):
    coupon = get_object_or_404(Coupon, pk=pk)
    coupon.is_active = not coupon.is_active
    coupon.save()
    status_str = "activated" if coupon.is_active else "deactivated"
    messages.info(request, f"Coupon '{coupon.code}' {status_str}.")
    return redirect('portal:coupons')


@admin_required
def reviews_view(request):
    reviews = Review.objects.select_related('product', 'user').order_by('-created_at')
    return render(request, 'portal/reviews.html', {'reviews': reviews})


@admin_required
def toggle_review_approval(request, pk):
    review = get_object_or_404(Review, pk=pk)
    review.is_approved = not review.is_approved
    review.save()
    review.product.update_rating_stats()
    status_str = "approved" if review.is_approved else "hidden"
    messages.info(request, f"Review has been {status_str}.")
    return redirect('portal:reviews')
