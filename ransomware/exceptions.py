# Custom exception types for ransomware PoC

class RansomwareError(Exception):
    """
    Base exception for ransomware package.
    """
    pass

class NetworkError(RansomwareError):
    """
    Raised for network-related errors.
    """
    pass

class EncryptionError(RansomwareError):
    """
    Raised for encryption/decryption errors.
    """
    pass

class DiscoveryError(RansomwareError):
    """
    Raised for file discovery errors.
    """
    pass 