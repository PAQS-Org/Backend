import base64
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding 
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding as asym_padding
import os
from django.conf import settings
class EncryptionUtil:
    
    @staticmethod
    def load_private_key():
        private_key_str = settings.PRIVATE_KEY
        if not private_key_str:
            raise ValueError("Private key is not set in Django settings.")
        return serialization.load_pem_private_key(
            private_key_str.encode(),
            password=None,
            backend=default_backend()
        )

    @staticmethod
    def load_public_key():
        public_key_str = settings.PUBLIC_KEY
        if not public_key_str:
            raise ValueError("Public key is not set in Django settings.")
        return serialization.load_pem_public_key(
            public_key_str.encode(),
            backend=default_backend()
        )

    @staticmethod
    def encrypt(data, public_key_str):
        """Encrypt data using the public key."""
        public_key = EncryptionUtil.load_public_key(public_key_str)
        encrypted = public_key.encrypt(
            data.encode(),
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return base64.b64encode(encrypted).decode('utf-8')

    @staticmethod
    def decrypt(encrypted_data, private_key_str):
        """Decrypt data using the private key."""
        encrypted_data_bytes = base64.b64decode(encrypted_data)
        private_key = EncryptionUtil.load_private_key(private_key_str)
        decrypted = private_key.decrypt(
            encrypted_data_bytes,
            asym_padding.OAEP(
                mgf=asym_padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        return decrypted.decode('utf-8')

    @staticmethod
    def rotate_key(data, old_private_key_str, new_public_key_str):
        """Rotate keys by decrypting with the old private key and encrypting with the new public key."""
        decrypted_data = EncryptionUtil.decrypt(data, old_private_key_str)
        return EncryptionUtil.encrypt(decrypted_data, new_public_key_str)
    
    

    # @staticmethod
    # def generate_rsa_key_pair():
    #     private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend())
    #     public_key = private_key.public_key()
    #     return private_key, public_key

    # @staticmethod
    # def encrypt_with_public_key(data, public_key):
    #     return public_key.encrypt(
    #         data,
    #         asym_padding.PKCS1v15()
    #     )
        
    # @staticmethod
    # def decrypt_with_private_key(encrypted_data, private_key):
    #     return private_key.decrypt(
    #         encrypted_data,
    #         asym_padding.PKCS1v15()
        
