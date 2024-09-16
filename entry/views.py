from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from cryptography.hazmat.primitives import serialization
from PAQSBackend.encry import EncryptionUtil
from cryptography.hazmat.backends import default_backend
import base64
from datetime import datetime

from django.http import HttpResponse


def index(request):
    now = datetime.now()
    html = f'''
    <html>
        <body>
            <h1>Hello from PAQS Team!</h1> 
            <h3>This is a trial</h3>
            <p>The current time is { now }.</p>
            <h3>test by osahene lab</h3>
        </body>
    </html>
    ''' 
    return HttpResponse(html)



class KeyExchangeView(APIView):
    def post(self, request):
        public_key_b64 = request.data.get('public_key')
        
        if not public_key_b64:
            return Response({'error': 'Public key not provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            public_key_bytes = base64.b64decode(public_key_b64)
            print('p-key', public_key_bytes)
            public_key = serialization.load_pem_public_key(public_key_bytes, backend=default_backend())

            # Generate AES key
            aes_key = EncryptionUtil.generate_key()
            print('aes', aes_key)

            # Encrypt AES key with client's public RSA key
            encrypted_aes_key = EncryptionUtil.encrypt_with_public_key(aes_key, public_key)
            
            # Encode the encrypted AES key in base64 to send to frontend
            encrypted_aes_key_b64 = base64.b64encode(encrypted_aes_key).decode('utf-8')
            print  ('enc', encrypted_aes_key_b64)

            return Response({'encrypted_key': encrypted_aes_key_b64}, status=status.HTTP_200_OK)

        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
