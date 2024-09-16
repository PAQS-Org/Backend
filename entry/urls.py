from django.urls import path
from .views import index, KeyExchangeView

urlpatterns = [
    path("", index),
    path('key-exchange/', KeyExchangeView.as_view(), name='key-exchange'),
    
]

