from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib import messages
from decimal import Decimal
from products.models import Product
from .models import Cart, CartItem, Coupon
from .utils import get_cart

def cart_detail_view(request):
    cart = get_cart(request)
    # Check if coupon is still valid for current subtotal
    if cart.coupon:
        valid, msg = cart.coupon.is_valid(cart.subtotal)
        if not valid:
            cart.coupon = None
            cart.save()
            messages.warning(request, f"Coupon removed: {msg}")

    # Recommended products
    recommended_products = Product.objects.filter(
        is_active=True,
        stock__gt=0
    ).exclude(id__in=[item.product.id for item in cart.items.all()])[:4]

    context = {
        'cart': cart,
        'items': cart.items.select_related('product'),
        'recommended_products': recommended_products,
    }
    return render(request, 'cart/cart_detail.html', context)


def add_to_cart_view(request, product_id):
    product = get_object_or_404(Product, id=product_id, is_active=True)
    cart = get_cart(request)

    if not product.is_in_stock:
        if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
            return JsonResponse({'success': False, 'message': f"Sorry, {product.name} is currently out of stock."})
        messages.error(request, f"Sorry, {product.name} is currently out of stock.")
        return redirect('products:detail', slug=product.slug)

    quantity = 1
    if request.method == 'POST':
        try:
            quantity = int(request.POST.get('quantity', 1))
        except (ValueError, TypeError):
            quantity = 1
    elif request.GET.get('quantity'):
        try:
            quantity = int(request.GET.get('quantity', 1))
        except (ValueError, TypeError):
            quantity = 1

    quantity = max(1, quantity)

    cart_item, created = CartItem.objects.get_or_create(
        cart=cart,
        product=product,
        defaults={'quantity': quantity}
    )

    if not created:
        new_qty = cart_item.quantity + quantity
        if new_qty > product.stock:
            new_qty = product.stock
            messages.warning(request, f"Limited to maximum available stock ({product.stock} units) for {product.name}.")
        cart_item.quantity = new_qty
        cart_item.save()
    else:
        if cart_item.quantity > product.stock:
            cart_item.quantity = product.stock
            cart_item.save()

    msg = f"Added {cart_item.quantity}x {product.name} to your cart!"

    # Buy Now redirect
    buy_now = request.POST.get('buy_now') or request.GET.get('buy_now')
    if buy_now == '1':
        return redirect('orders:checkout')

    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('ajax') == '1':
        return JsonResponse({
            'success': True,
            'message': msg,
            'cart_items_count': cart.total_items,
            'cart_subtotal': str(cart.subtotal),
        })

    messages.success(request, msg)
    referer = request.META.get('HTTP_REFERER')
    return redirect(referer or 'cart:detail')


def update_cart_quantity_view(request, item_id):
    cart = get_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)

    if request.method == 'POST':
        action = request.POST.get('action')
        new_quantity = request.POST.get('quantity')

        if action == 'increase':
            if cart_item.quantity < cart_item.product.stock:
                cart_item.quantity += 1
                cart_item.save()
            else:
                messages.warning(request, f"Only {cart_item.product.stock} units available in stock.")
        elif action == 'decrease':
            if cart_item.quantity > 1:
                cart_item.quantity -= 1
                cart_item.save()
            else:
                cart_item.delete()
                messages.info(request, f"Removed {cart_item.product.name} from your cart.")
        elif new_quantity is not None:
            try:
                qty = int(new_quantity)
                if qty <= 0:
                    cart_item.delete()
                else:
                    cart_item.quantity = min(qty, cart_item.product.stock)
                    cart_item.save()
            except (ValueError, TypeError):
                pass

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        # Re-fetch cart for fresh properties
        cart.refresh_from_db()
        return JsonResponse({
            'success': True,
            'cart_items_count': cart.total_items,
            'subtotal': str(cart.subtotal),
            'discount': str(cart.discount_amount),
            'shipping': str(cart.shipping_cost),
            'final_total': str(cart.final_total),
        })

    return redirect('cart:detail')


def remove_from_cart_view(request, item_id):
    cart = get_cart(request)
    cart_item = get_object_or_404(CartItem, id=item_id, cart=cart)
    product_name = cart_item.product.name
    cart_item.delete()

    messages.info(request, f"'{product_name}' was removed from your cart.")
    return redirect('cart:detail')


def apply_coupon_view(request):
    cart = get_cart(request)
    if request.method == 'POST':
        code = request.POST.get('coupon_code', '').strip().upper()
        if not code:
            messages.error(request, "Please enter a coupon code.")
            return redirect('cart:detail')

        try:
            coupon = Coupon.objects.get(code=code)
            is_valid, reason = coupon.is_valid(cart.subtotal)
            if is_valid:
                cart.coupon = coupon
                cart.save()
                messages.success(request, f"Coupon '{code}' applied successfully! Saved ₹{coupon.calculate_discount(cart.subtotal)}.")
            else:
                messages.error(request, f"Coupon could not be applied: {reason}")
        except Coupon.DoesNotExist:
            messages.error(request, f"Invalid coupon code '{code}'.")

    return redirect('cart:detail')


def remove_coupon_view(request):
    cart = get_cart(request)
    if cart.coupon:
        code = cart.coupon.code
        cart.coupon = None
        cart.save()
        messages.info(request, f"Coupon '{code}' removed from cart.")
    return redirect('cart:detail')
