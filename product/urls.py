from django.urls import path
from .views import ScanInfoView, CheckoutInfoView

urlpatterns = [
    path('qrinfo/', ScanInfoView.as_view(), name='qr_info'),
    path('checkoutinfo/', CheckoutInfoView.as_view(), name='checkout_info'),
    # path('generate/', GenerateAndLogQR.as_view, name='generate'),
]
