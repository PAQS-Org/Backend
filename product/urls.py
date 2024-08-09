from django.urls import path
from .views import  (
    GenerateAndLogQR
    )

urlpatterns = [
    path('generate/', GenerateAndLogQR.as_view, name='generate'),
]
