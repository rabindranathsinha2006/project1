from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('deals/', views.deals_view, name='deals'),
    path('about/', views.about_view, name='about'),
    path('contact/', views.contact_view, name='contact'),
    path('privacy/', views.privacy_view, name='privacy'),
    path('terms/', views.terms_view, name='terms'),
    path('api/check-pincode/', views.check_pincode_api, name='check_pincode'),
    path('api/newsletter/', views.newsletter_subscribe_api, name='newsletter'),
]
