from .utils import get_cart

def cart_context(request):
    try:
        cart = get_cart(request)
        return {
            'cart': cart,
            'cart_items_count': cart.total_items,
            'cart_subtotal': cart.subtotal,
        }
    except Exception:
        return {
            'cart': None,
            'cart_items_count': 0,
            'cart_subtotal': 0,
        }
