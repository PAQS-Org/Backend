from django.core.management.base import BaseCommand
from entry.models import KeyManagement
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives import serialization

class Command(BaseCommand):
    help = 'Rotate RSA keys'

    def handle(self, *args, **kwargs):
        # Generate new RSA key pair
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public_key = private_key.public_key()

        # Convert keys to PEM format
        private_pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.TraditionalOpenSSL,
            encryption_algorithm=serialization.NoEncryption()
        ).decode('utf-8')

        public_pem = public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo
        ).decode('utf-8')

        # Save the new key to KeyManagement with an incremented version
        latest_version = KeyManagement.objects.order_by('-version').first().version
        new_version = latest_version + 1

        KeyManagement.objects.create(version=new_version, public_key=public_pem, private_key=private_pem)

        self.stdout.write(self.style.SUCCESS(f'Successfully rotated keys to version {new_version}'))
