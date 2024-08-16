from django.urls import path
from .views import  (
    verify_payment, 
    InitiatePayment, 
    InvoiceViewSet, 
    CheckPaymentStatus,
    QRCodeViewSet,
    get_user_file,
    # download_receipt
    )

urlpatterns = [
    path('invoice/', InvoiceViewSet.as_view({'get':'list'}), name='invoice'),
    path('qrdata/', QRCodeViewSet.as_view({'get':'list'}), name='qrdata'),
    path('qrcodes/<str:company_name>/<str:product_name>/<str:batch_number>/<str:uuid>/', get_user_file, name='qrcodes'),
    path("initiate-payment/", InitiatePayment.as_view(), name='initiate-payment'),
    path("check-payment/", CheckPaymentStatus.as_view(), name='check-payment'),
    path("verify-payment/", verify_payment, name="verify_payment"),
    # path('receipt/<str:transaction_id>/', download_receipt, name='generate_receipt'),
]
