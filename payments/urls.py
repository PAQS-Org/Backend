from django.urls import path
from .views import  (
                    # initiate_payment, 
                    verify_payment, 
                    InitiatePayment
                    )

urlpatterns = [
    # path("initiate-payment/", initiate_payment, name="initiate_payment"),
    path("initiate-payment/", InitiatePayment.as_view(), name='initiate-payment'),
    path("verify-payment/", verify_payment, name="verify_payment"),
]
