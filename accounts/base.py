from django.contrib.auth.backends import BaseBackend
from django.contrib.auth.hashers import check_password
from accounts.models import User, Company

class CustomUserCompanyAuthBackend(BaseBackend):
    def authenticate(self, request, email=None, password=None, **kwargs):
        # Try to authenticate as a User
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            pass

        # Try to authenticate as a Company
        try:
            company = Company.objects.get(email=email)
            if company.check_password(password):
                return company
        except Company.DoesNotExist:
            pass

        return None

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            try:
                return Company.objects.get(pk=user_id)
            except Company.DoesNotExist:
                return None