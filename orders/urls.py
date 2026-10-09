from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout_view, name='checkout'),
    path('place-order/', views.place_order_view, name='place_order'),
    path('confirmation/<str:order_number>/', views.order_confirmation_view, name='confirmation'),
    path('track/<str:order_number>/', views.order_tracking_view, name='tracking'),
    path('cancel/<str:order_number>/', views.cancel_order_view, name='cancel'),
    path('my-orders/', views.user_orders_list_view, name='my_orders'),
]
