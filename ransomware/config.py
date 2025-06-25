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
    extension: Optional[str] = ".wasted"
    host: Optional[str] = "127.0.0.1"
    port: Optional[int] = 8080
    payment_address: Optional[str] = "1BitcoinEaterAddressDontSendf59kuE"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "allow" 