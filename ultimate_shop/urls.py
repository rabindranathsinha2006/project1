"""
ultimate_shop URL Configuration
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from products.views import product_list_view

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('', include('accounts.urls')),
    path('products/', include('products.urls')),
    # Direct shortcut for search
    path('search/', product_list_view, name='search'),
    path('cart/', include('cart.urls')),
    path('orders/', include('orders.urls')),
    path('assistant/', include('assistant.urls')),
    path('ai-assistant/', include(('assistant.urls', 'ai_assistant'), namespace='ai_page')),
    path('admin-portal/', include('portal.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
