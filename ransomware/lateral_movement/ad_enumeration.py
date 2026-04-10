#!/usr/bin/env python3
"""
Active Directory enumeration module.
Discovers domain information, users, and computers.
"""

import os
import platform
import socket
import subprocess
from typing import Dict, List, Optional

from ransomware.logging import logger


class ADEnumerator:
    """
    Enumerate Active Directory domain.
    """

    def __init__(self):
        self.is_windows = platform.system() == "Windows"
        self.domain_info: Dict = {}

    def is_domain_joined(self) -> bool:
        """Check if computer is joined to a domain."""
        if not self.is_windows:
            return False

        try:
            import ctypes
            computer_name = os.environ.get('COMPUTERNAME', '')

            # Check if we can get domain name
            result = subprocess.run(
                ["powershell", "-Command",
                 "(Get-WmiObject -Class Win32_ComputerSystem).Domain"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                domain = result.stdout.strip()
                return domain and domain != computer_name

        except Exception:
            pass

        return False

    def enumerate_domain(self) -> Dict:
        """
        Enumerate domain information.
        """
        if not self.is_domain_joined():
            logger.info("Computer not joined to domain")
            return {}

        self.domain_info = {
            'domain': self._get_domain_name(),
            'domain_controller': self._get_domain_controller(),
            'computers': self._enumerate_computers(),
            'users': self._enumerate_users(),
            'groups': self._enumerate_groups(),
            'shares': self._enumerate_domain_shares(),
            'ou_structure': self._enumerate_ous(),
        }

        return self.domain_info

    def _get_domain_name(self) -> Optional[str]:
        """Get current domain name."""
        try:
            result = subprocess.run(
                ["powershell", "-Command",
                 "(Get-WmiObject -Class Win32_ComputerSystem).Domain"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                return result.stdout.strip()

        except Exception:
            pass

        return None

    def _get_domain_controller(self) -> Optional[str]:
        """Get domain controller."""
        try:
            result = subprocess.run(
                ["nltest", "/dsgetdc:"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                # Parse DC name
                for line in result.stdout.splitlines():
                    if "DC:" in line:
                        return line.split("DC:")[1].strip()

        except Exception:
            pass

        return None

    def _enumerate_computers(self) -> List[str]:
        """
        Enumerate computers in domain.
        """
        computers = []

        try:
            # Use net view to find computers
            result = subprocess.run(
                ["net", "view", "/domain"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                # Parse computer names
                for line in result.stdout.splitlines():
                    if "\\" in line:
                        computer = line.strip().strip('\\')
                        computers.append(computer)

        except Exception as e:
            logger.error(f"Computer enumeration error: {e}")

        return computers

    def _enumerate_users(self) -> List[str]:
        """
        Enumerate domain users.
        """
        users = []

        try:
            # This requires domain admin or specific privileges
            result = subprocess.run(
                ["net", "user", "/domain"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                # Parse user list
                in_user_list = False
                for line in result.stdout.splitlines():
                    if "---" in line:
                        in_user_list = True
                        continue
                    if in_user_list and line.strip():
                        users.extend([u.strip() for u in line.split() if u.strip()])

        except Exception as e:
            logger.error(f"User enumeration error: {e}")

        return users

    def _enumerate_groups(self) -> List[str]:
        """
        Enumerate domain groups.
        """
        groups = []

        try:
            result = subprocess.run(
                ["net", "group", "/domain"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                in_group_list = False
                for line in result.stdout.splitlines():
                    if "---" in line:
                        in_group_list = True
                        continue
                    if in_group_list and line.strip():
                        groups.extend([g.strip() for g in line.split() if g.strip()])

        except Exception as e:
            logger.error(f"Group enumeration error: {e}")

        return groups

    def _enumerate_domain_shares(self) -> List[str]:
        """
        Enumerate domain shares.
        """
        shares = []

        try:
            # Use net view to find shares on each computer
            computers = self._enumerate_computers()

            for computer in computers[:10]:  # Limit to first 10
                try:
                    result = subprocess.run(
                        ["net", "view", f"\\\\{computer}"],
                        capture_output=True,
                        text=True,
                        timeout=5
                    )

                    if result.returncode == 0:
                        for line in result.stdout.splitlines():
                            if "Disk" in line:
                                share_name = line.split()[0].strip()
                                shares.append(f"\\\\{computer}\\{share_name}")

                except Exception:
                    pass

        except Exception as e:
            logger.error(f"Share enumeration error: {e}")

        return shares

    def _enumerate_ous(self) -> List[str]:
        """
        Enumerate Organizational Units.
        """
        ous = []

        try:
            # Requires RSAT tools or dsquery
            result = subprocess.run(
                ["dsquery", "ou", "/o", "domainroot"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                ous = [line.strip() for line in result.stdout.splitlines() if line.strip()]

        except Exception:
            # dsquery may not be available
            pass

        return ous

    def find_domain_admins(self) -> List[str]:
        """
        Find domain admin users.
        """
        admins = []

        try:
            result = subprocess.run(
                ["net", "group", "Domain Admins", "/domain"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                in_member_list = False
                for line in result.stdout.splitlines():
                    if "Members" in line:
                        in_member_list = True
                        continue
                    if in_member_list and line.strip() and "---" not in line:
                        admins.extend([a.strip() for a in line.split() if a.strip()])

        except Exception as e:
            logger.error(f"Domain admin enumeration error: {e}")

        return admins

    def get_spn_accounts(self) -> List[str]:
        """
        Find accounts with Service Principal Names (kerberoastable).
        """
        spn_accounts = []

        try:
            # Requires PowerShell ActiveDirectory module
            result = subprocess.run(
                ["powershell", "-Command",
                 "Get-ADUser -Filter {ServicePrincipalName -ne '$null'} -Properties ServicePrincipalName | Select Name, ServicePrincipalName"],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                logger.info("SPN accounts found (kerberoastable)")

        except Exception:
            pass

        return spn_accounts

    def get_report(self) -> str:
        """Generate AD enumeration report."""
        if not self.domain_info:
            self.enumerate_domain()

        report = []
        report.append("=" * 60)
        report.append("ACTIVE DIRECTORY ENUMERATION REPORT")
        report.append("=" * 60)
        report.append(f"Domain: {self.domain_info.get('domain', 'N/A')}")
        report.append(f"Domain Controller: {self.domain_info.get('domain_controller', 'N/A')}")
        report.append(f"Computers: {len(self.domain_info.get('computers', []))}")
        report.append(f"Users: {len(self.domain_info.get('users', []))}")
        report.append(f"Groups: {len(self.domain_info.get('groups', []))}")
        report.append(f"Shares: {len(self.domain_info.get('shares', []))}")
        report.append(f"OUs: {len(self.domain_info.get('ou_structure', []))}")
        report.append("=" * 60)

        return "\n".join(report)


if __name__ == "__main__":
    print("Active Directory Enumeration Test")
    print("=" * 60)

    enumerator = ADEnumerator()

    if enumerator.is_domain_joined():
        print("[+] Computer is domain joined")
        print("\n[*] Enumerating domain...")

        info = enumerator.enumerate_domain()

        print(f"[+] Domain: {info.get('domain')}")
        print(f"[+] Domain Controller: {info.get('domain_controller')}")
        print(f"[+] Computers found: {len(info.get('computers', []))}")
        print(f"[+] Users found: {len(info.get('users', []))}")
        print(f"[+] Groups found: {len(info.get('groups', []))}")

        print("\n[*] Finding Domain Admins...")
        admins = enumerator.find_domain_admins()
        print(f"[+] Domain Admins: {admins}")

        print("\n[*] Full Report:")
        print(enumerator.get_report())
    else:
        print("[!] Computer is not domain joined")
