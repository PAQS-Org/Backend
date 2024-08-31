from rest_framework import serializers
from django.core.validators import EmailValidator
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.contrib.auth import authenticate, password_validation
from rest_framework.exceptions import AuthenticationFailed
import boto3
from django.conf import settings
from django.utils.encoding import force_str
from django.utils.http import urlsafe_base64_decode
from .models import User, Company
import random


'''''
User Stuff
'''''''''


class RegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[EmailValidator(message='Enter a valid email address')]
    )
    password = serializers.CharField(
        write_only=True, required=True, validators=[password_validation.validate_password]
    )

    class Meta:
        model = User
        fields = ['first_name','last_name' ,'email', 'password']

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        # Send verification email here (if applicable)
        return user




class LoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(max_length=255, min_length=3)
    password = serializers.CharField(
        max_length=68, min_length=6, write_only=True)
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)

    tokens = serializers.SerializerMethodField()

    def get_tokens(self, obj):
        user = User.objects.get(email=obj['email'])

        return {
            'refresh': user.tokens()['refresh'],
            'access': user.tokens()['access']
        }

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password', 'tokens']
    
    def validate(self, attrs):
        email = attrs.get('email', '')
        password = attrs.get('password', '')
        filtered_user_by_email = User.objects.filter(email=email)
        user = authenticate(email=email, password=password)
        users = User.objects.get(email=email)

        if filtered_user_by_email.exists() and filtered_user_by_email[0].auth_provider != 'email':
            raise AuthenticationFailed(
                detail='Please continue your login using ' + filtered_user_by_email[0].auth_provider)

        if not user:
            raise AuthenticationFailed('Invalid credentials, try again')
        if not user.is_active:
            raise AuthenticationFailed('Account disabled, contact admin')
        if not user.is_verified:
            raise AuthenticationFailed('Email is not verified')

        return {
            'email': user.email,
            'first_name': users.first_name,
            'last_name': users.last_name,
            'tokens': user.tokens
        }

        return super().validate(attrs)


class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(
        min_length=6, max_length=68, write_only=True)
    token = serializers.CharField(
        min_length=1, write_only=True)
    uidb64 = serializers.CharField(
        min_length=1, write_only=True)

    class Meta:
        fields = ['password', 'token', 'uidb64']

    def validate(self, attrs):
        try:
            password = attrs.get('password')
            token = attrs.get('token')
            uidb64 = attrs.get('uidb64')

            id = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(id=id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationFailed('The reset link is invalid', 401)

            user.set_password(password)
            user.save()

            return (user)
        except Exception as e:
            raise AuthenticationFailed('The reset link is invalid', 401)
        return super().validate(attrs)
    

'''''
General Stuff
'''''''''

class ResetPasswordEmailRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(min_length=2)

    redirect_url = serializers.CharField(max_length=500, required=False)
    class Meta:
        fields = ['email']


class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField()

    def validate_token(self, value):
        try:
            # Implement token validation logic here (e.g., checking validity period)
            pass
        except Exception as e:
            raise serializers.ValidationError('Invalid verification token')
        return value


'''''
Company Stuff
'''''''''
class CompanyRegisterSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        validators=[EmailValidator(message='Enter a valid email address')],
    )
    password = serializers.CharField(
        write_only=True, required=True, validators=[password_validation.validate_password]
    )

    class Meta:
        model = Company
        fields = ['email', 'first_name', 'last_name', 'company_name', 'company_logo', 'password']

    def generate_unique_company_code(self):
        while True:
            code = random.randint(000000, 999999)
            if not Company.objects.filter(company_code=code).exists():
                return code
    
    def create(self, validated_data):
        # company = Company.objects.create_company(**validated_data)
        validated_data['company_code'] = self.generate_unique_company_code()
        company = Company.objects.create_user(**validated_data)
        # Send verification email here (if applicable)
        return company
    
def get_presigned_url(s3_key):
    s3 = boto3.client('s3', 
                      aws_access_key_id=settings.AWS_ACCESS_KEY_ID, 
                      aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY, 
                      region_name=settings.AWS_S3_REGION_NAME)
    presigned_url = s3.generate_presigned_url('get_object',
                                              Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                                                      'Key': s3_key},
                                              ExpiresIn=3600)  # URL valid for 1 hour
    return presigned_url

class CompanyLoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        max_length=255, validators=[EmailValidator(message='Enter a valid email address')]
    )
    password = serializers.CharField(write_only=True)
    company_name = serializers.CharField(read_only=True)  # Access company name from related field
    company_logo = serializers.SerializerMethodField()
    first_name = serializers.CharField(read_only=True)
    last_name = serializers.CharField(read_only=True)
    tokens = serializers.SerializerMethodField()

    def get_tokens(self, obj):
        user = Company.objects.get(email=obj['email'])

        return {
            'refresh': user.tokens()['refresh'],
            'access': user.tokens()['access']
        }
        
    def get_company_logo(self, obj):
        if obj.company_logo:
            return get_presigned_url(obj.company_logo.name)
        
    class Meta:
        model = Company
        fields = ['email', 'password', 'tokens', 'first_name', 'last_name', 'company_name', 'company_logo' ]

    def validate(self, attrs):
        email = attrs.get('email', '')
        password = attrs.get('password', '')
        filtered_user_by_email = Company.objects.filter(email=email)
        user = authenticate(email=email, password=password)
        users = Company.objects.get(email=email)

        if filtered_user_by_email.exists() and filtered_user_by_email[0].auth_provider != 'email':
            raise AuthenticationFailed(
                detail='Please continue your login using ' + filtered_user_by_email[0].auth_provider)

        if not user:
            raise AuthenticationFailed('Invalid credentials, try again')
        if not user.is_active:
            raise AuthenticationFailed('Account disabled, contact admin')
        if not user.is_verified:
            raise AuthenticationFailed('Email is not verified')
        if not user.is_company:
            raise AuthenticationFailed('This is not a company email')

        return {
            'email': user.email,
            'company_name': users.company_name,
            'company_logo': users.company_logo,
            'first_name': users.first_name,
            'last_name': users.last_name,
            'tokens': user.tokens
        }

        return super().validate(attrs)


class CompanySetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(
        min_length=6, max_length=68, write_only=True)
    token = serializers.CharField(
        min_length=1, write_only=True)
    uidb64 = serializers.CharField(
        min_length=1, write_only=True)

    class Meta:
        fields = ['password', 'token', 'uidb64']

    def validate(self, attrs):
        try:
            password = attrs.get('password')
            token = attrs.get('token')
            uidb64 = attrs.get('uidb64')

            id = force_str(urlsafe_base64_decode(uidb64))
            user = Company.objects.get(id=id)
            if not PasswordResetTokenGenerator().check_token(user, token):
                raise AuthenticationFailed('The reset link is invalid', 401)

            user.set_password(password)
            user.save()

            return (user)
        except Exception as e:
            raise AuthenticationFailed('The reset link is invalid', 401)
        return super().validate(attrs)