from .models import Category, Wishlist

def categories_context(request):
    return {
        'nav_categories': Category.objects.all()[:10],
    }

def wishlist_compare_context(request):
    wishlist_count = 0
    if request.user.is_authenticated:
        wishlist_count = Wishlist.objects.filter(user=request.user).count()
    else:
        wishlist_count = len(request.session.get('guest_wishlist', []))

    compare_list = request.session.get('compare_list', [])
    return {
        'wishlist_count': wishlist_count,
        'compare_count': len(compare_list),
    }
