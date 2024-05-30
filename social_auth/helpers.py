import requests as r
from google.auth.transport import requests
from google.oauth2 import id_token
from accounts.models import User
from django.contrib.auth import authenticate
from PAQSBackend.settings import GOOGLE_CLIENT_ID, SOCIAL_AUTH_PASSWORD
from rest_framework.exceptions import AuthenticationFailed



class Google():
    @staticmethod
    def validate(access_token):

        t = f"https://www.googleapis.com/oauth2/v3/tokeninfo?access_token={access_token}"
        response = r.get(t)

        if response.status_code != 200:
            raise AuthenticationFailed("The token is either invalid or has expired")

        token_info = response.json()
        if token_info.get('aud') != GOOGLE_CLIENT_ID:
            raise AuthenticationFailed("Invalid audience")
        
        if not token_info.get('email_verified', False):
            raise AuthenticationFailed("Email not verified by Google")

        return token_info
    

    @staticmethod
    def get_user_info(access_token):
        # Get user profile information using the People API
        people_api_url = "https://people.googleapis.com/v1/people/me?personFields=names,emailAddresses"
        headers = {"Authorization": f"Bearer {access_token}"}
        response = r.get(people_api_url, headers=headers)
        print(response)

        if response.status_code != 200:
            raise AuthenticationFailed("Failed to fetch user info from Google People API")

        user_info = response.json()
        names = user_info.get('names', [{}])
        email_addresses = user_info.get('emailAddresses', [{}])

        if not names or not email_addresses:
            raise AuthenticationFailed("Failed to retrieve necessary user info")

        first_name = names[0].get('givenName', '')
        last_name = names[0].get('familyName', '')
        email = email_addresses[0].get('value', '')

        return first_name, last_name, email






def register_social_user(provider, email, first_name, last_name):
    old_user=User.objects.filter(email=email)
    if old_user.exists():
        if provider == old_user[0].auth_provider:
            register_user=authenticate(email=email, password=SOCIAL_AUTH_PASSWORD)

            return {
                # 'full_name':User.objects.get(first_name),
                'email':register_user.email,
                'tokens':register_user.tokens()
            }
        else:
            raise AuthenticationFailed(
                detail=f"please continue your login with {old_user[0].auth_provider}"
            )
    else:
        new_user={
            'email':email,
            'first_name':first_name,
            'last_name':last_name,
            'password':SOCIAL_AUTH_PASSWORD
        }
        user=User.objects.create_user(**new_user)
        user.auth_provider=provider
        user.is_verified=True
        user.save()
        login_user=authenticate(email=email, password=SOCIAL_AUTH_PASSWORD)
       
        tokens=login_user.tokens()
        return {
            'email':login_user.email,
            # 'full_name':User.get_full_name(),
            "access_token":str(tokens.get('access')),
            "refresh_token":str(tokens.get('refresh'))
        }
