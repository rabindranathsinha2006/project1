from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail_view, name='detail'),
    path('add/<int:product_id>/', views.add_to_cart_view, name='add'),
    path('update/<int:item_id>/', views.update_cart_quantity_view, name='update'),
    path('remove/<int:item_id>/', views.remove_from_cart_view, name='remove'),
    path('apply-coupon/', views.apply_coupon_view, name='apply_coupon'),
    path('remove-coupon/', views.remove_coupon_view, name='remove_coupon'),
]
