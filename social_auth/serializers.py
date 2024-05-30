from rest_framework import serializers
from .helpers import Google, register_social_user
from PAQSBackend.settings import GOOGLE_CLIENT_ID
from rest_framework.exceptions import AuthenticationFailed


class GoogleSignInSerializer(serializers.Serializer):
    access_token=serializers.CharField()


    def validate_access_token(self, access_token):
        user_data=Google.validate(access_token)
        first_name, last_name, email = Google.get_user_info(access_token)
        
        print(first_name)


        try:
            user_data['sub']
            
        except:
            raise serializers.ValidationError("this token has expired or invalid please try again lil tee")
        
        if user_data['aud'] != GOOGLE_CLIENT_ID:
                raise AuthenticationFailed('Could not verify user.')

        email=email
        first_name=first_name
        last_name=last_name
        provider='google'

        return register_social_user(provider, email, first_name, last_name)

