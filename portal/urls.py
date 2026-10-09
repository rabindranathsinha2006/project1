from django.urls import path
from . import views

app_name = 'portal'

urlpatterns = [
    path('', views.dashboard_view, name='dashboard'),
    path('products/', views.products_list_view, name='products'),
    path('products/create/', views.product_form_view, name='product_create'),
    path('products/<int:pk>/edit/', views.product_form_view, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete_view, name='product_delete'),
    path('inventory/', views.inventory_view, name='inventory'),
    path('orders/', views.orders_list_view, name='orders'),
    path('orders/<str:order_number>/', views.order_detail_view, name='order_detail'),
    path('analytics/', views.analytics_view, name='analytics'),
    path('coupons/', views.coupons_view, name='coupons'),
    path('coupons/<int:pk>/toggle/', views.toggle_coupon_status, name='coupon_toggle'),
    path('reviews/', views.reviews_view, name='reviews'),
    path('reviews/<int:pk>/toggle/', views.toggle_review_approval, name='review_toggle'),
]
