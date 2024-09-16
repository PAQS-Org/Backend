import base64
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import padding, hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
import os

class EncryptionUtil:
    BLOCK_SIZE = 128  # Block size for AES
    IV_SIZE = 16      # Initialization Vector size
    KEY_SIZE = 32     # AES key size (256 bits)

    @staticmethod
    def generate_key():
        """Generate a random AES key."""
        return os.urandom(EncryptionUtil.KEY_SIZE)

    @staticmethod
    def encrypt(plain_text, key):
        """Encrypt the given plaintext with the provided key."""
        iv = os.urandom(EncryptionUtil.IV_SIZE)
        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        encryptor = cipher.encryptor()

        padder = padding.PKCS7(EncryptionUtil.BLOCK_SIZE).padder()
        padded_data = padder.update(plain_text.encode()) + padder.finalize()

        encrypted = encryptor.update(padded_data) + encryptor.finalize()
        return base64.b64encode(iv + encrypted).decode('utf-8')

    @staticmethod
    def decrypt(cipher_text, key):
        """Decrypt the given ciphertext with the provided key."""
        cipher_data = base64.b64decode(cipher_text)
        iv = cipher_data[:EncryptionUtil.IV_SIZE]
        encrypted_data = cipher_data[EncryptionUtil.IV_SIZE:]

        cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
        decryptor = cipher.decryptor()

        decrypted_padded = decryptor.update(encrypted_data) + decryptor.finalize()
        unpadder = padding.PKCS7(EncryptionUtil.BLOCK_SIZE).unpadder()
        decrypted = unpadder.update(decrypted_padded) + unpadder.finalize()

        return decrypted.decode('utf-8')

    @staticmethod
    def rotate_key(data, old_key, new_key):
        """Re-encrypt the data with the new key."""
        decrypted_data = EncryptionUtil.decrypt(data, old_key)
        return EncryptionUtil.encrypt(decrypted_data, new_key)

    @staticmethod
    def generate_rsa_key_pair():
        private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048, backend=default_backend)
        public_key = private_key.public_key()
        return private_key, public_key
    
    @staticmethod
    def encrypt_with_public_key(data, public_key):
        return public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )
        
    @staticmethod
    def decrypt_with_private_key(encrypted_data, private_key):
        return private_key.decrypt(
            encrypted_data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None
            )
        )