from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.hkdf import HKDF
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives.kdf.kbkdf import KBKDFHMAC
from cryptography.hazmat.primitives.kdf.concatkdf import ConcatKDFHash
from base64 import urlsafe_b64encode, urlsafe_b64decode
import os

# Key size and iterations configuration
KEY_SIZE = 32
ITERATIONS = 100_000

def generate_rsa_key_pair():
    """
    Generate RSA key pair (private and public keys).
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    public_key = private_key.public_key()
    return private_key, public_key

def serialize_public_key(public_key):
    """
    Serialize the public key to PEM format for sharing.
    """
    return public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

def deserialize_public_key(pem_public_key):
    """
    Deserialize the public key from PEM format.
    """
    return serialization.load_pem_public_key(
        pem_public_key,
        backend=default_backend()
    )

def serialize_private_key(private_key):
    """
    Serialize the private key to PEM format for secure storage.
    """
    return private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )

def decrypt_session_key(private_key, encrypted_session_key):
    """
    Decrypt the session key using the RSA private key.
    """
    return private_key.decrypt(
        encrypted_session_key,
        padding.OAEP(
            mgf=padding.MGF1(algorithm=hashes.SHA256()),
            algorithm=hashes.SHA256(),
            label=None
        )
    )

def encrypt_data(session_key, data):
    """
    Encrypt data using the session key and AES algorithm.
    """
    iv = os.urandom(16)  # Initialization vector for AES
    cipher = Cipher(
        algorithms.AES(session_key),
        modes.CFB(iv),
        backend=default_backend()
    )
    encryptor = cipher.encryptor()
    encrypted_data = encryptor.update(data.encode()) + encryptor.finalize()
    return iv + encrypted_data  # Return IV with encrypted data

def decrypt_data(session_key, encrypted_data):
    """
    Decrypt data using the session key and AES algorithm.
    """
    iv = encrypted_data[:16]
    cipher = Cipher(
        algorithms.AES(session_key),
        modes.CFB(iv),
        backend=default_backend()
    )
    decryptor = cipher.decryptor()
    decrypted_data = decryptor.update(encrypted_data[16:]) + decryptor.finalize()
    return decrypted_data.decode()
