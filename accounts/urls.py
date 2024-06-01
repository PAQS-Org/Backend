from django.urls import path
from .views import (
    CompanyRegistrationView, 
    LogoutAPIView, 
    SetNewPasswordAPIView, 
    EmailVerificationView, 
    CompanyLoginView, 
    IndividualLoginView,
    IndividualRegistrationView,
    )
# PasswordTokenCheckAPI, RequestPasswordResetEmail
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)


urlpatterns = [
    path('company-register/', CompanyRegistrationView.as_view(), name="register"),
    path('company-login/', CompanyLoginView.as_view(), name="login"),
    path('logout/', LogoutAPIView.as_view(), name="logout"),
    path('email-verify/', EmailVerificationView.as_view(), name="email-verify"),
    path('user-register/', IndividualRegistrationView.as_view(), name="user-register"),
    path('user-login', IndividualLoginView.as_view(), name="user-login"),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    # path('request-reset-email/', RequestPasswordResetEmail.as_view(),
    #      name="request-reset-email"),
    # path('password-reset/<uidb64>/<token>/',
    #      PasswordTokenCheckAPI.as_view(), name='password-reset-confirm'),
    path('password-reset-complete', SetNewPasswordAPIView.as_view(),
         name='password-reset-complete')
]