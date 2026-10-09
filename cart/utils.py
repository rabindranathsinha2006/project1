from .models import Cart, CartItem

def get_cart(request):
    if not request.session.session_key:
        request.session.save()
    session_key = request.session.session_key

    if request.user.is_authenticated:
        cart, _ = Cart.objects.get_or_create(user=request.user)
    else:
        cart, _ = Cart.objects.get_or_create(session_key=session_key, user=None)
    return cart

def merge_guest_cart(request, user):
    if not request.session.session_key:
        return
    session_key = request.session.session_key
    try:
        guest_cart = Cart.objects.filter(session_key=session_key, user=None).first()
        if guest_cart:
            user_cart, _ = Cart.objects.get_or_create(user=user)
            for item in guest_cart.items.all():
                user_item, created = CartItem.objects.get_or_create(
                    cart=user_cart,
                    product=item.product,
                    defaults={'quantity': item.quantity}
                )
                if not created:
                    user_item.quantity = min(user_item.quantity + item.quantity, item.product.stock)
                    user_item.save()
            # If guest cart had coupon, preserve it
            if guest_cart.coupon and not user_cart.coupon:
                user_cart.coupon = guest_cart.coupon
                user_cart.save()
            guest_cart.delete()
    except Exception:
        pass
