import requests
from django.shortcuts import render
import os
import jwt
import datetime
from django.shortcuts import redirect
# Create your views here.
from rest_framework import status, generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Company, User
from .serializer import (
    CompanyRegisterSerializer, CompanyLoginSerializer, CompanySetNewPasswordSerializer,
    # General
    EmailVerificationSerializer, 
    ResetPasswordEmailRequestSerializer,
    # indi serializer
    LoginSerializer, RegisterSerializer, SetNewPasswordSerializer, 
)
from rest_framework_simplejwt.tokens import RefreshToken
from django.urls import reverse
from django.contrib.sites.shortcuts import get_current_site
from PAQSBackend.settings import SECRET_KEY
# from django.conf import settings
from .utils import Util
from django.utils.encoding import smart_str, force_str, smart_bytes, DjangoUnicodeDecodeError
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.http import HttpResponsePermanentRedirect

from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.response import Response

from django.http import JsonResponse
import json
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator
from .task import delete_unverified_user
from .otp_service import send_otp, verify_otp, send_sms
from django.shortcuts import get_object_or_404
from django.core.mail import send_mail
from django.conf import settings
class CompanyRegistrationView(APIView):
    permission_classes = [AllowAny]

    # @method_decorator(ratelimit(key='ip', rate='2/d', method='POST'))
    def post(self, request):
        serializer = CompanyRegisterSerializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
            user_data = serializer.data
            user = Company.objects.get(email=user_data['email'])

            # Generate verification token (replace with your preferred library)
            token = RefreshToken.for_user(user).access_token
            current_site = get_current_site(request).domain
            relativeLink = reverse('company-email-verify')
            absurl = 'http://' + current_site + relativeLink + "?token=" + str(token)

            template_path = 'company-verification-email.html'
            email_body = render_to_string(template_path, {
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'company_name': user.company_name,
                'verification_link': absurl,
                'current_year': datetime.datetime.now().year,
            })
            data = {'email_body': email_body, 'to_email': user.email,
                    'email_subject': 'Verify your email'}

            Util.send_email(data)
            print("del")
            task = delete_unverified_user.apply_async((user.id,), countdown=301)
            print(f"Task ID: {task.id}")
            return Response(user_data, status=status.HTTP_201_CREATED)

        except ValidationError as e:
            return Response({"error": e.detail}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class CompanyLoginView(APIView):
    serializer_class = CompanyLoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)



class CompanyRequestPasswordResetEmail(generics.GenericAPIView):
    serializer_class = ResetPasswordEmailRequestSerializer
    
    @method_decorator(ratelimit(key='ip', rate='3/h', method='POST'))
    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        email = request.data.get('email', '')

        if Company.objects.filter(email=email).exists():
            user = Company.objects.get(email=email)
            uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            current_site = get_current_site(
                request=request).domain
            relativeLink = reverse( 
                'company-password-reset-confirm', kwargs={'uidb64': uidb64, 'token': token})

            redirect_url = request.data.get('redirect_url', '')
            absurl = f'http://{current_site}{relativeLink}'
            template_path = 'company-reset-password.html'
            email_body = render_to_string(template_path, {             
                'email':user.email,
                'company_name': user.company_name,
                'reset_link': absurl +"?redirect_url="+redirect_url,
                'current_year': datetime.datetime.now().year,
            })
            data = {'email_body': email_body, 'to_email': user.email,
                    'email_subject': 'Reset your passsword'}
            Util.send_email(data)
        return Response(absurl, status=status.HTTP_200_OK)


class CompanySetNewPasswordAPIView(generics.GenericAPIView):
    serializer_class = CompanySetNewPasswordSerializer

    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'success': True, 'message': 'Password reset success'}, status=status.HTTP_200_OK)



class CompanyPasswordTokenCheckAPI(generics.GenericAPIView):
    serializer_class = CompanySetNewPasswordSerializer

    def get(self, request, uidb64, token):

        redirect_url = request.GET.get('redirect_url')

        try:
            id = smart_str(urlsafe_base64_decode(uidb64))
            user = Company.objects.get(id=id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                if len(redirect_url) > 3:
                    return CustomRedirect(redirect_url+'?token_valid=False')
                else:
                    return CustomRedirect(os.environ.get('FRONTEND_URL', '')+'?token_valid=False')

            if redirect_url and len(redirect_url) > 3:
                return CustomRedirect(redirect_url+'?token_valid=True&message=Credentials Valid&uidb64='+uidb64+'&token='+token)
            else:
                return CustomRedirect(os.environ.get('FRONTEND_URL', '')+'?token_valid=False')

        except DjangoUnicodeDecodeError as identifier:
            try:
                if not PasswordResetTokenGenerator().check_token(user):
                    return CustomRedirect(redirect_url+'?token_valid=False')
                    
            except UnboundLocalError as e:
                return Response({'error': 'Token is not valid, please request a new one'}, status=status.HTTP_400_BAD_REQUEST)



class CompanyEmailVerificationView(APIView):
    permission_classes = [AllowAny]

    serializer_class = EmailVerificationSerializer
    def get(self, request):
        token = str(request.GET.get('token'))
        set_key = str(SECRET_KEY)
        try:
            payload = jwt.decode(token, set_key, algorithms=["HS256"])
            user = Company.objects.get(id=payload['user_id'])
        except jwt.ExpiredSignatureError as identifier:
            return Response({'error': 'Activation Expired'}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.exceptions.DecodeError as identifier:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)    # Redirect to frontend login page
        if not user.is_verified:
            user.is_verified = True
            user.is_company = True
            user.save()
        return redirect('https://paqscompany.vercel.app/#/auth/login/')



# General Stuff

class CustomRedirect(HttpResponsePermanentRedirect):

    allowed_schemes = [os.environ.get('FRONTEND_URL'), 'http', 'https']

    
class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get('refresh')
        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except (RefreshToken.DoesNotExist, ValidationError):
                return Response({'Failed': 'The operation is invalid'},status=status.HTTP_404_NOT_FOUND)
                  # Ignore potential errors if token is invalid or blacklisted already
        return Response(status=status.HTTP_204_NO_CONTENT)




    # User work
class UserLoginView(APIView):
    serializer_class = LoginSerializer
    
    @method_decorator(ratelimit(key='ip', rate='3/d', method='POST'))
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UserRegistrationView(APIView):
    permission_classes = [AllowAny]

    @method_decorator(ratelimit(key='ip', rate='30/d', method='POST'))
    def post(self, request):
            
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Detect country code based on IP address
        # ip_address = request.META.get('REMOTE_ADDR')
        # print('ipaddress', ip_address)
        # response = requests.get(f'http://ipinfo.io/{ip_address}/json')
        # print('res', response)
        # country_code = response.json().get('country')
        # print('count', country_code)
        
        # # Append country code to the phone number
        # full_phone_number = f"+{get_country_code(country_code)}{user.phone_number}"
        # print('f_numb', full_phone_number)
        
        # Generate OTP and send to user's phone number
        otp = send_otp(user.phone_number)
        print('otp', otp)

        # Save the phone number with country code
        # user.phone_number = full_phone_number
        # print('use phone', user.phone_number)
        user.save()

        return Response({'message': 'OTP sent successfully'}, status=status.HTTP_201_CREATED)

class OTPVerificationView(APIView):
    def post(self, request):
        email = request.data.get('email')
        otp = request.data.get('otp')
        user = get_object_or_404(User, email=email)

        # Verify OTP
        success, message = verify_otp(user.phone_number, otp)
        if success:
            user.is_phone_verified = True
            user.is_verified = True
            user.save()

            # Send thank you message via SMS and email
            send_mail(
                "Welcome",
                "Thank you for joining us",
                settings.DEFAULT_FROM_EMAIL,
                [user.email],
                fail_silently=False,
            )
            send_sms(user.phone_number, "Thank you for joining us!")
            return Response({'message': 'User verified and registration complete'}, status=status.HTTP_200_OK)

        # Handle OTP failure cases
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)


# def get_country_code(country_code):
#     # You can add more countries here
#     country_codes = {'GH': '+233', 'NG': '+234', 'BF': '+226'}
#     return country_codes.get(country_code, '1')


class UserEmailVerificationView(APIView):
    permission_classes = [AllowAny]

    serializer_class = EmailVerificationSerializer
    
    @method_decorator(ratelimit(key='ip', rate='3/d', method='GET'))
    def get(self, request):
        token = str(request.GET.get('token'))
        set_key = str(SECRET_KEY)
        try:
            payload = jwt.decode(token, set_key, algorithms=["HS256"])
            user = User.objects.get(id=payload['user_id'])
        except jwt.ExpiredSignatureError as identifier:
            return Response({'error': 'Activation Expired'}, status=status.HTTP_400_BAD_REQUEST)
        except jwt.exceptions.DecodeError as identifier:
            return Response({'error': 'Invalid token'}, status=status.HTTP_400_BAD_REQUEST)    # Redirect to frontend login page
        if not user.is_verified:
            user.is_verified = True
            user.save()
        return redirect('https://paqs.vercel.app/#/auth/login/')
        

class UserRequestPasswordResetEmail(generics.GenericAPIView):
    serializer_class = ResetPasswordEmailRequestSerializer

    @method_decorator(ratelimit(key='ip', rate='3/d', method='POST'))
    def post(self, request):
        serializer = self.serializer_class(data=request.data)

        email = request.data.get('email', '')

        if User.objects.filter(email=email).exists():
            user = User.objects.get(email=email)
            uidb64 = urlsafe_base64_encode(smart_bytes(user.id))
            token = PasswordResetTokenGenerator().make_token(user)
            current_site = get_current_site(
                request=request).domain
            relativeLink = reverse( 
                'password-reset-confirm', kwargs={'uidb64': uidb64, 'token': token})

            redirect_url = request.data.get('redirect_url', '')
            absurl = f'http://{current_site}{relativeLink}'
            template_path = 'user-reset-password.html'
            email_body = render_to_string(template_path, {             
                'email':user.email,
                'reset_link': absurl +"?redirect_url="+redirect_url,
                'current_year': datetime.datetime.now().year,
            })
            data = {'email_body': email_body, 'to_email': user.email,
                    'email_subject': 'Reset your passsword'}
            Util.send_email(data)
        return Response(absurl, status=status.HTTP_200_OK)


class UserPasswordTokenCheckAPI(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def get(self, request, uidb64, token):

        redirect_url = request.GET.get('redirect_url')

        try:
            id = smart_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=id)

            if not PasswordResetTokenGenerator().check_token(user, token):
                if len(redirect_url) > 3:
                    return CustomRedirect(redirect_url+'?token_valid=False')
                else:
                    return CustomRedirect(os.environ.get('FRONTEND_URL', '')+'?token_valid=False')

            if redirect_url and len(redirect_url) > 3:
                return CustomRedirect(redirect_url+'?token_valid=True&message=Credentials Valid&uidb64='+uidb64+'&token='+token)
            else:
                return CustomRedirect(os.environ.get('FRONTEND_URL', '')+'?token_valid=False')

        except DjangoUnicodeDecodeError as identifier:
            try:
                if not PasswordResetTokenGenerator().check_token(user):
                    return CustomRedirect(redirect_url+'?token_valid=False')
                    
            except UnboundLocalError as e:
                return Response({'error': 'Token is not valid, please request a new one'}, status=status.HTTP_400_BAD_REQUEST)

class UserSetNewPasswordAPIView(generics.GenericAPIView):
    serializer_class = SetNewPasswordSerializer

    def patch(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response({'success': True, 'message': 'Password reset success'}, status=status.HTTP_200_OK)

def csp_report(request):
    if request.method == 'POST':
        report = json.loads(request.body.decode('utf-8'))
        # Process the report (e.g., log to a file, database, etc.)
        # For now, let's just print it
        print('csp', report)
        return JsonResponse({'status': 'ok'}, status=204)  # 204 No Content is a typical response
    return JsonResponse({'status': 'method not allowed'}, status=405)


class CustomTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        print('req', request)
        refresh = request.COOKIES.get('refresh')
        if not refresh:
            return Response({"error": "Refresh token is missing"}, status=400)
        
        # Pass the refresh token to SimpleJWT's validation
        data = {"refresh": refresh}
        request._full_data = data  # Mock request data for the SimpleJWT view

        response = super().post(request, *args, **kwargs)
        new_access_token = response.data['access']

        # Set the new access token in a HTTP-Only cookie
        response.set_cookie(
            key="refresh",
            value=new_access_token,
            httponly=True,
            secure=True,  # Use HTTPS in production
            samesite='Lax',
        )
        return response
