from rest_framework import serializers
from django.core.validators import EmailValidator
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.contrib.auth import authenticate, password_validation
from django.core.exceptions import ValidationError


from .models import User, Company


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


class EmailVerificationSerializer(serializers.Serializer):
    token = serializers.CharField()

    def validate_token(self, value):
        try:
            # Implement token validation logic here (e.g., checking validity period)
            pass
        except Exception as e:
            raise serializers.ValidationError('Invalid verification token')
        return value


class LoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        max_length=255, validators=[EmailValidator(message='Enter a valid email address')]
    )
    password = serializers.CharField(write_only=True)
    tokens = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['email', 'password', 'tokens']

    def get_tokens(self, obj):
        user = authenticate(email=obj['email'], password=obj['password'])
        if not user:
            raise serializers.ValidationError('Invalid credentials')
        if not user.is_active:
            raise serializers.ValidationError('Account disabled')
        refresh = RefreshToken.for_user(user)
        return {'refresh': str(refresh), 'access': str(refresh.access_token)}


class ResetPasswordEmailRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(
        validators=[EmailValidator(message='Enter a valid email address')]
    )

    def validate_email(self, value):
        # Check if email exists in the system
        # Send reset password email here
        return value


class SetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, validators=[password_validation.validate_password])
    token = serializers.CharField(write_only=True)
    uidb64 = serializers.CharField(write_only=True)

    def validate(self, attrs):
        try:
            password = attrs.get('password')
            token = attrs.get('token')
            user = RefreshToken(token).user  # Access user object from verified token
            if not user.is_active:
                raise serializers.ValidationError('Account disabled')
            if not isinstance(user, User):  # Check if user is a Company object
                raise serializers.ValidationError('Invalid token for company password reset')
            user.set_password(password)
            user.save()
            return user
        except Exception as e:
            raise serializers.ValidationError('Invalid token or user type')


class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    def validate(self, attrs):
        try:
            refresh = RefreshToken(attrs['refresh'])
            refresh.blacklist()
        except TokenError:
            raise serializers.ValidationError('Invalid refresh token')
        return attrs


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

    def create(self, validated_data):
        company = Company.objects.create_company(**validated_data)
        # Send verification email here (if applicable)
        return company


class CompanyLoginSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
        max_length=255, validators=[EmailValidator(message='Enter a valid email address')]
    )
    password = serializers.CharField(write_only=True)
    company_name = serializers.ReadOnlyField(source='name')  # Access company name from related field
    company_logo = serializers.ReadOnlyField(source='logo') 
    tokens = serializers.SerializerMethodField()

    class Meta:
        model = Company
        fields = ['email', 'password', 'tokens', 'company_name', 'company_logo' ]

    def get_tokens(self, obj):
        user = authenticate(email=obj['email'], password=obj['password'])
        if not user:
            raise serializers.ValidationError('Invalid credentials')
        if not user.is_active:
            raise serializers.ValidationError('Account disabled')
        refresh = RefreshToken.for_user(user)
        return {'refresh': str(refresh),
                'access': str(refresh.access_token),
                }


class CompanyResetPasswordEmailRequestSerializer(serializers.Serializer):
    email = serializers.EmailField(
        validators=[EmailValidator(message='Enter a valid email address')]
    )

    def validate_email(self, value):
        # Check if email exists in the system
        # Send reset password email here
        return value


class CompanySetNewPasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True, validators=[password_validation.validate_password])
    token = serializers.CharField(write_only=True)
    uidb64 = serializers.CharField(write_only=True)

    def validate(self, attrs):
        try:
            password = attrs.get('password')
            token = attrs.get('token')
            user = RefreshToken(token).user  # Access user object from verified token
            if not user.is_active:
                raise serializers.ValidationError('Account disabled')
            if not isinstance(user, Company):  # Check if user is a Company object
                raise serializers.ValidationError('Invalid token for company password reset')
            user.set_password(password)
            user.save()
            return user
        except Exception as e:
            raise serializers.ValidationError('Invalid token or user type')