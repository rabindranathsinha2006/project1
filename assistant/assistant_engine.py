import re
from decimal import Decimal
from django.db.models import Q
from products.models import Product, Category

SYNONYM_CATEGORY_MAP = {
    'smartphone': 'electronics',
    'smartphones': 'electronics',
    'phone': 'electronics',
    'phones': 'electronics',
    'mobile': 'electronics',
    'laptop': 'electronics',
    'laptops': 'electronics',
    'earphone': 'electronics',
    'earphones': 'electronics',
    'headphone': 'electronics',
    'headphones': 'electronics',
    'audio': 'electronics',
    'shoes': 'fashion',
    'sneakers': 'fashion',
    'jacket': 'fashion',
    'apparel': 'fashion',
    'clothing': 'fashion',
    'watch': 'fashion',
    'purifier': 'home-kitchen',
    'espresso': 'home-kitchen',
    'coffee': 'home-kitchen',
    'skincare': 'beauty-wellness',
    'serum': 'beauty-wellness',
    'dumbbells': 'sports-fitness',
    'fitness': 'sports-fitness',
}

def parse_price_constraint(query):
    query_lower = query.lower().replace(',', '')
    
    # Check 'between X and Y'
    between_match = re.search(r'between\s+(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(?:and|to|-)\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)', query_lower)
    if between_match:
        try:
            return Decimal(between_match.group(1)), Decimal(between_match.group(2))
        except Exception:
            pass

    # Check 'under / below / less than / cheaper than / budget'
    under_match = re.search(r'(?:under|below|less than|cheaper than|budget|within|upto|up to)\s*(?:₹|rs\.?|inr)?\s*(\d+(?:\.\d+)?)\s*(k)?', query_lower)
    if under_match:
        try:
            val = Decimal(under_match.group(1))
            if under_match.group(2) == 'k':
                val *= 1000
            return Decimal('0'), val
        except Exception:
            pass

    return None, None

def search_assistant_products(query):
    query_clean = query.strip()
    query_lower = query_clean.lower()

    min_price, max_price = parse_price_constraint(query)

    products_qs = Product.objects.filter(is_active=True).select_related('category')

    # Price bounds check (using effective price or price)
    if min_price is not None and max_price is not None:
        products_qs = products_qs.filter(
            Q(discount_price__gte=min_price, discount_price__lte=max_price) |
            Q(discount_price__isnull=True, price__gte=min_price, price__lte=max_price)
        )
    elif max_price is not None:
        products_qs = products_qs.filter(
            Q(discount_price__lte=max_price) |
            Q(discount_price__isnull=True, price__lte=max_price)
        )

    # Detect categories or synonyms
    matched_categories = []
    for cat in Category.objects.all():
        if cat.name.lower() in query_lower or cat.slug.lower() in query_lower:
            matched_categories.append(cat)

    if not matched_categories:
        for keyword, cat_slug in SYNONYM_CATEGORY_MAP.items():
            if keyword in query_lower:
                cat = Category.objects.filter(slug__icontains=cat_slug).first()
                if cat and cat not in matched_categories:
                    matched_categories.append(cat)

    if matched_categories:
        cat_filtered = products_qs.filter(category__in=matched_categories)
        if cat_filtered.exists():
            products_qs = cat_filtered

    # Detect brand keywords
    all_brands = Product.objects.values_list('brand', flat=True).distinct()
    matched_brand = None
    for b in all_brands:
        if b and b.lower() in query_lower:
            matched_brand = b
            products_qs = products_qs.filter(brand__iexact=b)
            break

    # Keyword search across name and description
    words = [w for w in re.findall(r'\b[a-zA-Z0-9]+\b', query_lower) if w not in [
        'find', 'the', 'best', 'under', 'for', 'in', 'me', 'show', 'a', 'an', 'what', 'is', 'good', 'cheap', 'to', 'buy', 'rs', 'inr'
    ]]

    if words:
        word_query = Q()
        for word in words:
            word_query |= Q(name__icontains=word) | Q(description__icontains=word) | Q(short_description__icontains=word) | Q(brand__icontains=word)
        filtered_by_words = products_qs.filter(word_query)
        if filtered_by_words.exists():
            products_qs = filtered_by_words

    # Prioritize in-stock items first!
    products_qs = products_qs.order_by('-stock', '-average_rating', '-is_bestseller')

    # Preference ranking
    if 'best' in query_lower or 'top' in query_lower or 'rating' in query_lower:
        products_qs = products_qs.order_by('-stock', '-average_rating', '-review_count')
    elif 'deal' in query_lower or 'discount' in query_lower or 'offer' in query_lower:
        products_qs = products_qs.filter(discount_price__isnull=False).order_by('-stock', '-discount_price')
    elif 'cheap' in query_lower or 'affordable' in query_lower or 'low' in query_lower:
        products_qs = products_qs.order_by('-stock', 'price')
    elif 'bestseller' in query_lower or 'popular' in query_lower:
        products_qs = products_qs.order_by('-stock', '-is_bestseller', '-review_count')

    results = list(products_qs[:5])
    return results, min_price, max_price, matched_brand

def generate_assistant_response(query):
    results, min_p, max_p, brand = search_assistant_products(query)

    if not results:
        popular = list(Product.objects.filter(is_active=True, stock__gt=0).order_by('-is_bestseller', '-average_rating')[:3])
        return {
            'text': f"I couldn't find exact matches for \"{query}\", but here are some of our customer favorites you might love:",
            'products': [format_product_data(p) for p in popular],
            'suggestions': [
                "Find smartphones under ₹20,000",
                "Best rated noise cancelling headphones",
                "Show trending fashion deals",
                "Laptops for work and coding"
            ]
        }

    details = []
    if max_p:
        details.append(f"budget under ₹{max_p:,.0f}")
    if brand:
        details.append(f"from {brand}")

    criteria_str = f" with {' and '.join(details)}" if details else ""
    text = f"Here are the best matching products{criteria_str} curated from our catalog:"

    suggestions = [
        "Show me bestsellers under ₹2,000",
        "Compare top rated items",
        "Show deals with 30%+ discount",
        "Check my order status"
    ]

    return {
        'text': text,
        'products': [format_product_data(p) for p in results],
        'suggestions': suggestions
    }

def format_product_data(product):
    return {
        'id': product.id,
        'name': product.name,
        'brand': product.brand,
        'category': product.category.name,
        'slug': product.slug,
        'price': f"{product.price:,.2f}",
        'discount_price': f"{product.discount_price:,.2f}" if product.discount_price else None,
        'effective_price': f"{product.effective_price:,.2f}",
        'discount_percent': product.discount_percent,
        'rating': float(product.average_rating),
        'reviews': product.review_count,
        'image': product.primary_image,
        'in_stock': product.is_in_stock,
        'detail_url': f"/products/product/{product.slug}/",
        'add_cart_url': f"/cart/add/{product.id}/",
    }
