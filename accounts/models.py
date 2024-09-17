# Create your models here.
from django.db import models
from django.core.validators import EmailValidator
from django.urls import reverse
from django.contrib.auth.models import (
    AbstractBaseUser, BaseUserManager, PermissionsMixin)
from rest_framework_simplejwt.tokens import RefreshToken
from django.core.validators import RegexValidator

AUTH_PROVIDERS = {'facebook': 'facebook', 'google': 'google',
                  'twitter': 'twitter', 'email': 'email', 'otp':'otp'}


class UserManager(BaseUserManager):

    def create_user(self, email, phone_number=None, password=None, **extra_fields):
        """
        Creates and saves a User with the given email and password.
        """
        if not email:
            raise ValueError('Users must have an email address')
        if not phone_number:
            raise ValueError('Users must have a phone number')
        email = self.normalize_email(email)
        user = self.model(email=email, phone_number=phone_number, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        """
        Creates and saves a superuser with the given email and password.
        """
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_staff', True)

        if not email:
            raise ValueError('Superusers must have an email address')
        if not password:
            raise ValueError('Superusers must have a password')

        return self.create_user(email, password, **extra_fields)


class AbstractUserProfile(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(
        verbose_name='email address',
        max_length=255,
        unique=True,
        validators=[EmailValidator()],  # Ensure valid email format
    )
    phone_regex = RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Phone number must be entered in the format: '+999999999'. Up to 15 digits allowed.")
    phone_number = models.CharField(validators=[phone_regex], max_length=17, blank=True)
    is_phone_verified = models.BooleanField(default=False)
    
    is_verified = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    auth_provider = models.CharField(
        max_length=255, blank=False, null=False, default=AUTH_PROVIDERS.get('email')
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['phone_number']  # No additional fields required for base user

    objects = UserManager()
    
    class Meta:
        indexes = [
            models.Index(fields=['email', 'phone_number'])
        ]

    def __str__(self):
        return self.email

    def tokens(self):
        refresh = RefreshToken.for_user(self)
        return {'refresh': str(refresh), 'access': str(refresh.access_token)}
    
    def get_short_name(self):
        return self.email
    
class Company(AbstractUserProfile):
    first_name = models.CharField(max_length=100, db_index=True)
    last_name = models.CharField(max_length=100, db_index=True)
    company_name = models.CharField(max_length=255, db_index=True, unique=True)
    company_logo = models.ImageField(upload_to='paqs/comp_logo/', blank=True)  # Optional logo
    is_company = models.BooleanField(default=False)
    company_code = models.PositiveIntegerField(null=True, blank=True, unique=True)

    USERNAME_FIELD = "email"
    
    # objects = CompanyManager()

    class Meta:
        verbose_name = 'Company'
        verbose_name_plural = 'Companies'
        indexes = [
            models.Index(fields=['company_code'])
        ]

    def __str__(self):
        return self.company_name

    def get_absolute_url(self):
        return reverse('user-detail', kwargs={'pk': self.pk})  # Assuming a detail view

    def get_image(self):
        if self.company_logo:
            return self.company_logo.url
        return None  
    
    @property
    def get_full_name(self):
        return f"{self.first_name.title()} {self.last_name.title()}"
    
    def get_short_name(self):
        return self.first_name 
    

class User(AbstractUserProfile):
    first_name = models.CharField(max_length=100, db_index=True)
    last_name = models.CharField(max_length=100, db_index=True)

    objects = UserManager()
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        
    @property
    def get_full_name(self):
        return f"{self.first_name.title()} {self.last_name.title()}"
    
    def get_short_name(self):
        return self.first_name 