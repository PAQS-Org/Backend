from django.urls import path
from .views import ScanInfoView, CheckoutInfoView, PatchInfoView

urlpatterns = [
    path('qrinfo/', ScanInfoView.as_view(), name='qr_info'),
    path('checkoutinfo/', CheckoutInfoView.as_view(), name='checkout_info'),
    path('patchinfo/', PatchInfoView.as_view(), name='patch_info'),
]
