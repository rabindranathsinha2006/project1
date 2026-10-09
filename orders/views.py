from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import uuid

from cart.utils import get_cart
from cart.models import CartItem
from accounts.models import Address, UserProfile, LoyaltyTransaction
from products.models import Product
from .models import Order, OrderItem, OrderTracking

@login_required
def checkout_view(request):
    cart = get_cart(request)
    if cart.total_items == 0:
        messages.warning(request, "Your shopping cart is empty. Add items before proceeding to checkout.")
        return redirect('products:list')

    # Verify all cart items have enough stock
    for item in cart.items.all():
        if item.quantity > item.product.stock:
            messages.error(request, f"Sorry, only {item.product.stock} units of '{item.product.name}' are available. Please update your cart.")
            return redirect('cart:detail')

    addresses = Address.objects.filter(user=request.user)
    default_address = addresses.filter(is_default=True).first() or addresses.first()
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    # Max points redeemable (up to 20% of subtotal or current points, whichever is smaller)
    max_redeemable = min(profile.loyalty_points, int(cart.subtotal * Decimal('0.20')))

    context = {
        'cart': cart,
        'items': cart.items.select_related('product'),
        'addresses': addresses,
        'default_address': default_address,
        'profile': profile,
        'max_redeemable_points': max_redeemable,
    }
    return render(request, 'orders/checkout.html', context)


@login_required
def place_order_view(request):
    if request.method != 'POST':
        return redirect('orders:checkout')

    cart = get_cart(request)
    if cart.total_items == 0:
        messages.error(request, "Your cart is empty.")
        return redirect('products:list')

    # Address determination
    address_id = request.POST.get('address_id')
    shipping_address = None

    if address_id == 'new':
        full_name = request.POST.get('full_name', '').strip()
        phone = request.POST.get('phone', '').strip()
        street = request.POST.get('street_address', '').strip()
        city = request.POST.get('city', '').strip()
        state = request.POST.get('state', '').strip()
        postal_code = request.POST.get('postal_code', '').strip()

        if not (full_name and phone and street and city and state and postal_code):
            messages.error(request, "Please fill out all required shipping address fields.")
            return redirect('orders:checkout')

        shipping_address = Address.objects.create(
            user=request.user,
            full_name=full_name,
            phone=phone,
            street_address=street,
            apartment_suite=request.POST.get('apartment_suite', '').strip(),
            city=city,
            state=state,
            postal_code=postal_code,
            country='India',
            address_type='Home',
            is_default=not Address.objects.filter(user=request.user).exists()
        )
    else:
        try:
            shipping_address = Address.objects.get(id=int(address_id), user=request.user)
        except (Address.DoesNotExist, ValueError, TypeError):
            messages.error(request, "Please select a valid delivery address.")
            return redirect('orders:checkout')

    # Payment details
    payment_method = request.POST.get('payment_method', 'cod')
    if payment_method not in ['cod', 'online']:
        payment_method = 'cod'

    payment_status = 'pending'
    transaction_id = ''
    if payment_method == 'online':
        payment_status = 'completed'
        transaction_id = f"SIM-PAY-{uuid.uuid4().hex[:12].upper()}"

    # Points redemption
    redeem_points = 0
    loyalty_discount = Decimal('0.00')
    profile, _ = UserProfile.objects.get_or_create(user=request.user)

    if request.POST.get('redeem_loyalty') == '1':
        try:
            requested_pts = int(request.POST.get('points_to_redeem', 0))
            max_redeem = min(profile.loyalty_points, int(cart.subtotal * Decimal('0.20')))
            redeem_points = max(0, min(requested_pts, max_redeem))
            loyalty_discount = Decimal(str(redeem_points))  # ₹1 per point
        except (ValueError, TypeError):
            redeem_points = 0

    # Atomic transaction for stock safety and order creation
    try:
        with transaction.atomic():
            # 1. Lock and re-validate product stocks
            cart_items = list(cart.items.select_related('product').all())
            for item in cart_items:
                product = Product.objects.select_for_update().get(id=item.product.id)
                if product.stock < item.quantity:
                    raise ValueError(f"Insufficient stock for {product.name}. Available: {product.stock}")

            subtotal = cart.subtotal
            coupon_discount = cart.discount_amount
            coupon_code = cart.coupon.code if cart.coupon else ''
            shipping_cost = cart.shipping_cost
            final_total = max(Decimal('0.00'), subtotal - coupon_discount - loyalty_discount + shipping_cost)

            # Points earned: 1 point per ₹10 of total paid
            points_earned = int(final_total // 10)

            # Estimated delivery date (3-5 days ahead)
            est_delivery = timezone.now().date() + timedelta(days=4)

            # 2. Create Order
            order = Order.objects.create(
                user=request.user,
                status='placed',
                shipping_full_name=shipping_address.full_name,
                shipping_phone=shipping_address.phone,
                shipping_address=f"{shipping_address.street_address}{', ' + shipping_address.apartment_suite if shipping_address.apartment_suite else ''}",
                shipping_city=shipping_address.city,
                shipping_state=shipping_address.state,
                shipping_postal_code=shipping_address.postal_code,
                shipping_country=shipping_address.country,
                payment_method=payment_method,
                payment_status=payment_status,
                transaction_id=transaction_id,
                subtotal=subtotal,
                coupon_discount=coupon_discount,
                coupon_code=coupon_code,
                loyalty_discount=loyalty_discount,
                shipping_cost=shipping_cost,
                total_amount=final_total,
                points_earned=points_earned,
                points_redeemed=redeem_points,
                tracking_number=f"TRK-{uuid.uuid4().hex[:8].upper()}",
                estimated_delivery_date=est_delivery
            )

            # 3. Create OrderItems and deduct stock safely
            for item in cart_items:
                product = Product.objects.select_for_update().get(id=item.product.id)
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    product_name=product.name,
                    product_image=product.primary_image,
                    price=product.effective_price,
                    quantity=item.quantity,
                    total_price=item.line_total
                )
                product.stock -= item.quantity
                product.save(update_fields=['stock'])

            # 4. Handle loyalty points
            if redeem_points > 0:
                profile.loyalty_points -= redeem_points
                LoyaltyTransaction.objects.create(
                    user=request.user,
                    points=-redeem_points,
                    description=f"Redeemed points for Order #{order.order_number}"
                )

            if points_earned > 0:
                profile.loyalty_points += points_earned
                LoyaltyTransaction.objects.create(
                    user=request.user,
                    points=points_earned,
                    description=f"Earned points from Order #{order.order_number}"
                )
            profile.save()

            # 5. Increment coupon usage
            if cart.coupon:
                cart.coupon.times_used += 1
                cart.coupon.save(update_fields=['times_used'])

            # 6. Add initial tracking history
            OrderTracking.objects.create(
                order=order,
                status='placed',
                title="Order Placed Successfully",
                description="We have received your order and are preparing it for fulfillment.",
                location="Fulfillment Center"
            )

            # 7. Clear cart
            cart.items.all().delete()
            cart.coupon = None
            cart.save()

        messages.success(request, f"🎉 Order #{order.order_number} placed successfully!")
        return redirect('orders:confirmation', order_number=order.order_number)

    except ValueError as e:
        messages.error(request, str(e))
        return redirect('cart:detail')
    except Exception as e:
        messages.error(request, f"An unexpected error occurred during checkout: {str(e)}")
        return redirect('orders:checkout')


@login_required
def order_confirmation_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    items = order.items.all()
    context = {
        'order': order,
        'items': items,
    }
    return render(request, 'orders/confirmation.html', context)


@login_required
def order_tracking_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    items = order.items.all()
    logs = order.tracking_logs.all().order_by('timestamp')

    context = {
        'order': order,
        'items': items,
        'logs': logs,
    }
    return render(request, 'orders/tracking.html', context)


@login_required
def cancel_order_view(request, order_number):
    order = get_object_or_404(Order, order_number=order_number, user=request.user)
    if request.method == 'POST':
        if not order.is_cancellable:
            messages.error(request, f"Order #{order.order_number} cannot be cancelled because it is already {order.get_status_display().lower()}.")
            return redirect('orders:tracking', order_number=order.order_number)

        reason = request.POST.get('cancellation_reason', 'Cancelled by customer')

        try:
            with transaction.atomic():
                order.status = 'cancelled'
                order.cancellation_reason = reason
                order.save(update_fields=['status', 'cancellation_reason', 'updated_at'])

                # Restore inventory safely
                for item in order.items.all():
                    if item.product:
                        product = Product.objects.select_for_update().get(id=item.product.id)
                        product.stock += item.quantity
                        product.save(update_fields=['stock'])

                # Revert loyalty points
                profile, _ = UserProfile.objects.get_or_create(user=request.user)
                if order.points_redeemed > 0:
                    profile.loyalty_points += order.points_redeemed
                    LoyaltyTransaction.objects.create(
                        user=request.user,
                        points=order.points_redeemed,
                        description=f"Refunded points from cancelled Order #{order.order_number}"
                    )
                if order.points_earned > 0:
                    profile.loyalty_points = max(0, profile.loyalty_points - order.points_earned)
                    LoyaltyTransaction.objects.create(
                        user=request.user,
                        points=-order.points_earned,
                        description=f"Reversed earned points for cancelled Order #{order.order_number}"
                    )
                profile.save()

                OrderTracking.objects.create(
                    order=order,
                    status='cancelled',
                    title="Order Cancelled",
                    description=f"Order was cancelled. Reason: {reason}",
                    location="System"
                )

            messages.info(request, f"Order #{order.order_number} has been cancelled successfully. Your stock and reward points have been updated.")
        except Exception as e:
            messages.error(request, f"Error cancelling order: {str(e)}")

    return redirect('orders:tracking', order_number=order.order_number)


@login_required
def user_orders_list_view(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    status_filter = request.GET.get('status')
    if status_filter:
        orders = orders.filter(status=status_filter)

    return render(request, 'accounts/orders.html', {'orders': orders, 'status_filter': status_filter})
