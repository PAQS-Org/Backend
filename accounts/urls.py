from django.urls import path
from .views import (
    CompanyRegistrationView, 
    CompanyLoginView, 
    CompanyRequestPasswordResetEmail,
    CompanyPasswordTokenCheckAPI,
    CompanyEmailVerificationView, 
    CompanySetNewPasswordAPIView,
    # User
    UserSetNewPasswordAPIView,
    UserEmailVerificationView,
    UserPasswordTokenCheckAPI, 
    UserRequestPasswordResetEmail,
    UserLoginView,
    UserRegistrationView,
    # General
    LogoutAPIView,
    # csp report
    csp_report 
    )
from rest_framework_simplejwt.views import (
    TokenRefreshView,
)


urlpatterns = [
    path('company-register/', CompanyRegistrationView.as_view(), name="register"),
    path('company-login/', CompanyLoginView.as_view(), name="login"),
    path('company-request-reset-email/', CompanyRequestPasswordResetEmail.as_view(), name="company-request-reset-email"),
    path('company-password-reset/<uidb64>/<token>/', CompanyPasswordTokenCheckAPI.as_view(), name='company-password-reset-confirm'),
    path('company-email-verify/', CompanyEmailVerificationView.as_view(), name="company-email-verify"),
    path('company-password-reset/', CompanySetNewPasswordAPIView.as_view(), name='company-password-reset-complete'),
    # user
    path('user-register/', UserRegistrationView.as_view(), name="user-register"),
    path('user-login/', UserLoginView.as_view(), name="user-login"),
    path('user-request-reset-email/', UserRequestPasswordResetEmail.as_view(),name="user-request-reset-email"),
    path('password-reset/<uidb64>/<token>/', UserPasswordTokenCheckAPI.as_view(), name='password-reset-confirm'),
    path('user-email-verify/', UserEmailVerificationView.as_view(), name="user-email-verify"),
    path('user-password-reset/', UserSetNewPasswordAPIView.as_view(), name='password-reset-complete'),
    # generic
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('logout/', LogoutAPIView.as_view(), name="logout"),

    # csp report
    path('csp-report/', csp_report, name='csp_report'),
]