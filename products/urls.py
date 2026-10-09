from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('', views.product_list_view, name='list'),
    path('category/<slug:slug>/', views.category_detail_view, name='category'),
    path('product/<slug:slug>/', views.product_detail_view, name='detail'),
    path('product/<slug:slug>/reviews/', views.product_reviews_view, name='reviews'),
    path('product/<slug:slug>/add-review/', views.add_review_view, name='add_review'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.toggle_wishlist_view, name='toggle_wishlist'),
    path('compare/', views.compare_view, name='compare'),
    path('compare/toggle/<int:product_id>/', views.toggle_compare_view, name='toggle_compare'),
    path('compare/clear/', views.clear_compare_view, name='clear_compare'),
    path('price-alert/set/<int:product_id>/', views.set_price_alert_view, name='set_price_alert'),
    path('restock/notify/<int:product_id>/', views.restock_subscription_view, name='restock_notify'),
]
