from django.urls import path
from . import views

app_name = 'assistant'

urlpatterns = [
    path('', views.assistant_page_view, name='page'),
    path('chat/', views.assistant_chat_api, name='chat_api'),
]
