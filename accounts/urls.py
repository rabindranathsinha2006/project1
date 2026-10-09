from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.account_dashboard, name='dashboard'),
    path('profile/edit/', views.profile_update, name='profile_edit'),
    path('addresses/', views.addresses_list, name='addresses'),
    path('addresses/add/', views.address_create, name='address_add'),
    path('addresses/<int:pk>/edit/', views.address_edit, name='address_edit'),
    path('addresses/<int:pk>/delete/', views.address_delete, name='address_delete'),
    path('addresses/<int:pk>/default/', views.address_set_default, name='address_set_default'),
    path('price-alerts/', views.price_alerts_list, name='price_alerts'),
    path('price-alerts/<int:pk>/delete/', views.price_alert_delete, name='price_alert_delete'),
    path('loyalty-rewards/', views.loyalty_history, name='loyalty'),
]
