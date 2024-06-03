from django.shortcuts import render
import os
import datetime
# Create your views here.
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Company, User
from .serializer import (
    CompanyRegisterSerializer, CompanyLoginSerializer,
    EmailVerificationSerializer, SetNewPasswordSerializer,
    # indi serializer
    LoginSerializer, RegisterSerializer
)
from rest_framework_simplejwt.tokens import RefreshToken
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
from .utils import Util
from django.utils.encoding import smart_str, force_str, smart_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth.tokens import PasswordResetTokenGenerator

from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string



class CompanyRegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = CompanyRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # Generate verification token (replace with your preferred library)
        user_data = serializer.data
        user = Company.objects.get(email=user_data['email'])
        token = RefreshToken.for_user(user).access_token
        current_site = get_current_site(request).domain
        relativeLink = reverse('email-verify')
        absurl = 'http://'+current_site+relativeLink+"?token="+str(token)
        template_path = 'company-verification-email.html'
        email_body = render_to_string(template_path, {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'company_name': user.company_name,
            'verification_link': absurl,
            'current_year': datetime.datetime.now().year,
        })
        data = {'email_body': email_body, 'to_email': user.email,
                'email_subject': 'Verify your email'}

        Util.send_email(data)
        return Response(user_data, status=status.HTTP_201_CREATED)

class CompanyLoginView(APIView):
    serializer_class = CompanyLoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = Company.objects.get(email=email)

        refresh = RefreshToken.for_user(user)
        token_response = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
        if hasattr(user, 'company'):
            token_response.update({
                "company_name": user.company.company_name,
                "company_logo": user.company.get_image(),
            })

        return Response(token_response, status=status.HTTP_200_OK)

class EmailVerificationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['token']
        try:
            company_name = force_str(urlsafe_base64_decode(token))
            company = Company.objects.get(pk=company_name)
        except (ValueError, DjangoUnicodeDecodeError, Company.DoesNotExist):
            return Response({'error': 'Invalid verification token'}, status=status.HTTP_400_BAD_REQUEST)
        # Add verification logic (e.g., check token validity using a library)
        if not is_valid_verification_token(company, token):  # Replace with your verification logic
            return Response({'error': 'Invalid verification token'}, status=status.HTTP_400_BAD_REQUEST)
        company.is_active = True
        company.save()
        return Response({'message': 'Email verified successfully.'}, status=status.HTTP_200_OK)


class IndividualEmailVerificationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        token = serializer.validated_data['token']
        try:
            first_name = force_str(urlsafe_base64_decode(token))
            user = User.objects.get(pk=first_name)
        except (ValueError, DjangoUnicodeDecodeError, User.DoesNotExist):
            return Response({'error': 'Invalid verification token'}, status=status.HTTP_400_BAD_REQUEST)
        # Add verification logic (e.g., check token validity using a library)
        if not is_valid_verification_token(user, token):  # Replace with your verification logic
            return Response({'error': 'Invalid verification token'}, status=status.HTTP_400_BAD_REQUEST)
        user.is_active = True
        user.save()
        return Response({'message': 'Email verified successfully.'}, status=status.HTTP_200_OK)

def is_valid_verification_token(company, token):
    """
    Checks the validity of the verification token for the company.
    """
    generator = PasswordResetTokenGenerator()
    return generator.check_token(company, token)

class SetNewPasswordAPIView(APIView):
    def patch(self, request):
        serializer = SetNewPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user  # Access user from request object (assuming JWT authentication)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'success': True, 'message': 'Password reset success'}, status=status.HTTP_200_OK)


class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except (RefreshToken.DoesNotExist, ValidationError):
                pass  # Ignore potential errors if token is invalid or blacklisted already
        return Response(status=status.HTTP_204_NO_CONTENT)
    




    # Individuals work
class IndividualLoginView(APIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)

        refresh = RefreshToken.for_user(user)
        token_response = {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        }
        if hasattr(user, 'user'):
            token_response.update({
                "first_name": user.user.first_name,
                "last_name": user.user.last_name,
                "email": user.user.email,
            })

        return Response(token_response, status=status.HTTP_200_OK)


class IndividualRegistrationView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        # Generate verification token (replace with your preferred library)
        user_data = serializer.data
        user = User.objects.get(email=user_data['email'])
        token = RefreshToken.for_user(user).access_token
        current_site = get_current_site(request).domain
        relativeLink = reverse('user-email-verify')
        absurl = 'http://'+current_site+relativeLink+"?token="+str(token)
        template_path = 'verification-email.html'
        email_body = render_to_string(template_path, {
            'first_name': user.first_name,
            'last_name': user.last_name,
            'verification_link': absurl,
            'current_year': datetime.datetime.now().year,
        })
        data = {'email_body': email_body, 'to_email': user.email,
                'email_subject': 'Verify your email'}

        Util.send_email(data)
        return Response(user_data, status=status.HTTP_201_CREATED)