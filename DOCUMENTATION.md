# PainPain Ransomware PoC - Complete Technical Documentation

## Table of Contents
1. [Overview](#overview)
2. [Architecture](#architecture)
3. [Module Breakdown](#module-breakdown)
4. [Encryption Scheme](#encryption-scheme)
5. [Execution Flow](#execution-flow)
6. [C2 Communication](#c2-communication)
7. [Advanced Features](#advanced-features)
8. [Configuration](#configuration)
9. [Testing](#testing)
10. [Security Considerations](#security-considerations)

---

## Overview

PainPain is a modular, educational ransomware Proof-of-Concept (PoC) designed to demonstrate how modern ransomware operates. It implements realistic ransomware techniques including hybrid encryption, C2 (Command & Control) communication, file discovery, and a ransom GUI.

### Purpose
- **Educational**: Understanding ransomware mechanics for defense
- **Research**: Testing detection and prevention mechanisms
- **Training**: Cybersecurity awareness and incident response practice

### Key Capabilities
| Feature | Description |
|---------|-------------|
| Hybrid Encryption | RSA-2048 for key exchange + Fernet (AES-128-CBC) for files |
| File Discovery | Recursive directory traversal with extension filtering |
| C2 Communication | HTTP POST exfiltration to Flask server |
| Ransom GUI | Tkinter-based WannaCry-style interface |
| Persistence | Registry Run keys, startup folders (optional) |
| Lateral Movement | Network share enumeration (optional) |
| Evasion | VM detection, Defender bypass, event log clearing (optional) |

---

## Architecture

```
PainPain-Ransomware-PoC/
├── main.py                          # CLI entry point
├── generate_keys.py                 # RSA key pair generator
├── requirements.txt                 # Python dependencies
├── Dockerfile                       # Container configuration
├── .env.example                     # Environment template
├── README.md                        # Basic documentation
├── DOCUMENTATION.md                 # This file
│
├── ransomware/                      # Core ransomware package
│   ├── __init__.py
│   ├── config.py                    # Pydantic configuration
│   ├── core.py                      # Main orchestration class
│   ├── logging.py                   # Loguru setup
│   ├── exceptions.py                # Custom exceptions
│   ├── discover.py                  # Legacy discovery
│   ├── modify.py                    # In-place file modification
│   │
│   ├── crypto/                      # Encryption modules
│   │   ├── __init__.py
│   │   ├── encryptor.py             # Fernet encryption/decryption
│   │   └── keys.py                  # RSA key management
│   │
│   ├── discovery/                   # File discovery
│   │   ├── __init__.py
│   │   └── discoverer.py            # Recursive file finder
│   │
│   ├── network/                     # C2 communication
│   │   ├── __init__.py
│   │   └── client.py                # HTTP client for C2
│   │
│   ├── gui/                         # Ransom GUI
│   │   ├── __init__.py
│   │   └── main.py                  # Tkinter GUI (RansomwareGUI)
│   ├── gui_main.py                  # Legacy GUI (WannaCry-style)
│   ├── gui.py                       # Original GUI
│   │
│   ├── persistence.py               # Phase 2: Persistence
│   ├── spread.py                    # Phase 3: Lateral movement
│   ├── stealth.py                   # Phase 5: Evasion
│   └── utils.py                     # Phase 1: Shell helpers, VM detection
│
├── c2_server/                       # C2 Server
│   ├── c2_server.py                 # Socket-based server (legacy)
│   └── c2_server_alt.py             # Flask HTTP server (current)
│
├── tests/                           # Unit tests
│   ├── test_discovery.py
│   ├── test_encryptor.py
│   ├── test_gui.py
│   └── test_network.py
│
├── clean_dark_secure_folder.py      # Cleanup utility
└── testDir/                         # Test data
```

---

## Module Breakdown

### 1. main.py - Entry Point

**Location**: `main.py`

The main entry point for the ransomware agent. Handles CLI arguments, logging setup, and orchestrates execution.

```python
# Usage patterns
python main.py -p "./testDir/banking_receipts" -e    # Encrypt
python main.py -p "./testDir/banking_receipts" -d    # Decrypt
```

**Key Functions**:
- `setup_logging()`: Creates timestamped log files in `logs/`
- `parse_args()`: Handles `-p` (path), `-e` (encrypt), `-d` (decrypt), `--mid` (machine ID)
- `main()`: Initializes config and runs `RansomwareApp`

**Logging Information Captured**:
- Timestamp, platform, Python version, user, hostname
- All operations logged to `logs/ransomware_activity_YYYYMMDD_HHMMSS.log`

---

### 2. Core Orchestrator (ransomware/core.py)

**Location**: `ransomware/core.py`

The `RansomwareApp` class coordinates all ransomware operations.

```python
class RansomwareApp:
    def __init__(self, config: AppConfig)
    def get_machine_id(self) -> str                    # Unique victim ID
    def exfiltrate_to_c2(self, root_dir: str)           # Send data to C2
    def run_process(self, root_dir: str, ...)           # Main workflow
```

**Execution Modes**:

#### Encryption Mode (`encrypt=True`)
1. Fetch RSA public key from C2 (`/public_key`)
2. Generate unique Fernet key for this victim
3. Save Fernet key locally (for PoC recovery)
4. Discover files using `FileDiscoverer`
5. Encrypt each file and append `.wasted` extension
6. Encrypt Fernet key with RSA public key
7. Exfiltrate machine data + encrypted key to C2
8. Launch ransom GUI

#### Decryption Mode (`encrypt=False`)
1. Fetch plaintext Fernet key from C2 (`/fetch_key`)
2. Discover files with `.wasted` extension
3. Decrypt and restore original filenames
4. No GUI is shown in decryption mode

---

### 3. Configuration (ransomware/config.py)

**Location**: `ransomware/config.py`

Uses Pydantic Settings for type-safe configuration loading from `.env` files.

```python
class AppConfig(BaseSettings):
    c2_server_url: str                 # C2 endpoint
    encryption_key_path: str           # Local key storage
    log_level: str = "INFO"
    timeout: int = 30
    extension: str = ".wasted"
    payment_address: str                # BTC address for ransom
    
    # Feature flags for advanced phases
    enable_utils: bool = True
    enable_persistence: bool = False
    enable_spread: bool = False
    enable_c2_tls: bool = False
    enable_stealth: bool = False
```

**Environment Variables** (from `.env`):
```ini
C2_SERVER_URL=http://127.0.0.1:8080
ENCRYPTION_KEY_PATH=./encryption.key
RSA_PRIVATE_KEY_PATH=c2_private_key.pem
LOG_LEVEL=INFO
PAYMENT_ADDRESS=1BitcoinEaterAddressDontSendf59kuE
```

---

### 4. Encryption Module (ransomware/crypto/)

#### 4.1 encryptor.py

**Fernet Symmetric Encryption**:

Fernet uses AES-128 in CBC mode with PKCS7 padding and HMAC for authentication.

```python
class Encryptor:
    @staticmethod
    def generate_key() -> bytes          # 32-byte URL-safe base64 key
    def encrypt_file(self, file_path)    # In-place file encryption
    def decrypt_file(self, file_path)    # In-place file decryption
```

**Encryption Process**:
1. Read entire file into memory
2. Encrypt using `fernet.encrypt(data)`
3. Write encrypted data back to file
4. File is renamed with `.wasted` extension

#### 4.2 keys.py

**RSA Key Management**:

```python
class Keys:
    @staticmethod
    def load_key(path: str) -> bytes
    @staticmethod
    def save_key(path: str, key: bytes)
    @staticmethod
    def generate_rsa_keypair() -> tuple[bytes, bytes]  # (priv, pub)
    @staticmethod
    def encrypt_with_rsa(data: bytes, rsa_public_key_pem: bytes) -> bytes
    @staticmethod
    def decrypt_with_rsa(ciphertext_b64: bytes, rsa_private_key_pem: bytes) -> bytes
```

**RSA Implementation**:
- Key size: 2048 bits
- Padding: OAEP with SHA-256
- Output: Base64-encoded ciphertext

---

### 5. Discovery Module (ransomware/discovery/)

**Location**: `ransomware/discovery/discoverer.py`

```python
class FileDiscoverer:
    def __init__(self, root_dir: str, extensions: Optional[List[str]] = None)
    def discover_files(self) -> List[str]
```

**Features**:
- Recursive directory traversal using `os.walk()`
- Extension filtering (optional)
- Skips hidden files (`.*`)
- Skips key files (`.key`, `encryption.key`)

**Legacy Module** (`ransomware/discover.py`):
- Generator-based discovery
- Hardcoded extension list for common file types
- Yields absolute paths

---

### 6. Network Module (ransomware/network/)

**Location**: `ransomware/network/client.py`

```python
class NetworkClient:
    def __init__(self, config: AppConfig)
    def send_data(self, endpoint: str, data: dict) -> dict
    def fetch_public_key(self) -> str                    # GET /public_key
    def request_decrypt_key(self, machine_id: str) -> str  # POST /decrypt_key
    def fetch_decrypted_key(self, machine_id: str) -> str  # POST /fetch_key
```

**Endpoints**:
- `GET /public_key`: Retrieve RSA public key for encryption
- `POST /decrypt_key`: Request encrypted Fernet key (after payment)
- `POST /fetch_key`: Fetch plaintext Fernet key (post-payment confirmation)

---

### 7. GUI Module (ransomware/gui/)

**Location**: `ransomware/gui/main.py`

```python
class RansomwareGUI(tk.Tk):
    def __init__(self, target_dir=None, payment_address='...', decrypt_cmd=None)
    def build_gui(self)                      # Construct ransom note UI
    def update_timer(self)                   # Countdown timer (72 hours)
    def try_decrypt(self)                    # Validate code and decrypt
    def run_decrypt_command(self)            # Execute subprocess decryption
```

**GUI Features**:
- Black background with red/yellow text (WannaCry-style)
- Skull emoji/icon header
- Countdown timer: 72 hours
- Bitcoin payment address display
- Decryption code entry (`bitcoin` is hardcoded)
- Automatic window close after successful decryption

**Decryption Flow**:
1. User enters code "bitcoin"
2. GUI spawns subprocess: `python main.py -p <dir> -d --mid <machine_id>`
3. Waits for completion
4. Shows success message
5. Closes after 1 second

---

## Encryption Scheme

### Hybrid Encryption Architecture

PainPain uses a hybrid encryption scheme combining asymmetric (RSA) and symmetric (Fernet/AES) encryption:

```
┌─────────────────────────────────────────────────────────────────┐
│                        ENCRYPTION FLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────┐          ┌────────────────┐                   │
│  │ C2 Server    │          │ Victim Machine │                   │
│  │              │          │                │                   │
│  │ RSA Key Pair │          │                │                   │
│  │ - Private    │          │                │                   │
│  │ - Public     │◄─────────┤ 1. Fetch Pub   │                   │
│  └──────────────┘          │    Key         │                   │
│                            └────────────────┘                   │
│                                      │                          │
│                            ┌─────────▼──────────┐               │
│                            │ 2. Generate Fernet │               │
│                            │    Key (per-victim)│               │
│                            └─────────┬──────────┘               │
│                                      │                          │
│                            ┌─────────▼──────────┐               │
│                            │ 3. Encrypt Files    │               │
│                            │    with Fernet     │               │
│                            └─────────┬──────────┘               │
│                                      │                          │
│                            ┌─────────▼──────────┐               │
│                            │ 4. Encrypt Fernet │               │
│                            │    with RSA Pub   │               │
│                            └─────────┬──────────┘               │
│                                      │                          │
│  ┌──────────────┐          ┌─────────▼──────────┐               │
│  │ C2 Server    │◄─────────┤ 5. Exfiltrate     │               │
│  │ - Encrypted  │          │    Machine Data   │               │
│  │   Fernet Key │          │    + Encrypted Key│               │
│  └──────────────┘          └───────────────────┘               │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### Technical Details

#### Fernet Encryption
- **Algorithm**: AES-128-CBC with PKCS7 padding
- **Authentication**: HMAC-SHA256
- **Key**: 32 bytes, URL-safe base64-encoded
- **Token Format**: `version (1) + timestamp (8) + IV (16) + ciphertext + HMAC (32)`

#### RSA Encryption
- **Key Size**: 2048 bits
- **Padding**: OAEP (Optimal Asymmetric Encryption Padding)
- **Hash**: SHA-256 for both main hash and MGF
- **Use**: Encrypts the Fernet key (max 32 bytes → fits in 2048-bit RSA)

### Why Hybrid?

| Approach | Problem |
|----------|---------|
| Pure RSA | Too slow for large files; size limitations |
| Pure AES | Key distribution problem; same key for all |
| Hybrid | RSA protects the AES key; AES is fast for files |

---

## Execution Flow

### Encryption Sequence

```
main.py
    └── parse_args()
        └── AppConfig() loads from .env
            └── RansomwareApp(config)
                └── run_process(path, encrypt=True)
                    ├── 1. NetworkClient.fetch_public_key()
                    │       └── GET /public_key → RSA pub
                    ├── 2. Encryptor.generate_key() → Fernet
                    ├── 3. FileDiscoverer.discover_files()
                    │       └── os.walk(root_dir)
                    ├── 4. For each file:
                    │       ├── Encryptor.encrypt_file(file)
                    │       └── os.rename(file, file + ".wasted")
                    ├── 5. Keys.encrypt_with_rsa(fernet_key, rsa_pub)
                    ├── 6. exfiltrate_to_c2(root_dir)
                    │       └── POST /exfiltrate
                    └── 7. RansomwareGUI(target_dir, decrypt_cmd)
                            └── mainloop() - blocks until closed
```

### Decryption Sequence

```
main.py
    └── parse_args()
        └── RansomwareApp(config)
            └── run_process(path, encrypt=False, machine_id=...)
                ├── 1. NetworkClient.fetch_decrypted_key(machine_id)
                │       └── POST /fetch_key → Fernet key
                │       └── (Fallback: local .fernet_key file)
                ├── 2. FileDiscoverer.discover_files()
                ├── 3. For each .wasted file:
                │       ├── Encryptor.decrypt_file(file)
                │       └── os.rename(file, file[:-len(".wasted")])
                └── 4. Log completion
```

---

## C2 Communication

### Flask C2 Server (c2_server/c2_server_alt.py)

**Endpoints**:

#### `GET /public_key`
Returns the RSA public key for victim encryption.

```json
{
  "public_key": "-----BEGIN PUBLIC KEY-----\nMIIBIjANBgkqhki..."
}
```

#### `POST /exfiltrate`
Receives victim data and encrypted Fernet key.

**Request**:
```json
{
  "ip_address": "192.168.1.100",
  "operating_system": "Windows",
  "username": "john",
  "hostname": "DESKTOP-ABC123",
  "target_directory": "C:\\Users\\john\\Documents",
  "victim_fernet_key": "base64(RSA_encrypted_fernet_key)"
}
```

**Response**:
```json
{
  "status": "ok",
  "message": "Data received and exfiltration started"
}
```

**Side Effects**:
- Stores machine data in `c2_data/<machine_id>_<timestamp>.json`
- Starts background thread to copy files from `target_directory` to `darkSecureFolder/<machine_id>/`

#### `POST /decrypt_key`
Returns the RSA-encrypted Fernet key for a machine.

**Request**:
```json
{"machine_id": "192.168.1.100_DESKTOP-ABC123_john"}
```

**Response**:
```json
{"encrypted_key": "base64_encrypted_key"}
```

#### `POST /send_key`
Attacker endpoint to upload the decrypted Fernet key after payment.

**Request**:
```json
{
  "machine_id": "192.168.1.100_DESKTOP-ABC123_john",
  "fernet_key": "gAAAAABf..."
}
```

#### `POST /fetch_key`
Victim endpoint to retrieve the plaintext Fernet key after payment confirmation.

**Request**:
```json
{"machine_id": "192.168.1.100_DESKTOP-ABC123_john"}
```

**Response**:
```json
{"fernet_key": "gAAAAABf..."}
```

### Data Storage

```
darkSecureFolder/
└── <machine_id>/
    └── [copied files from victim's target directory]

c2_data/
└── <machine_id>_<timestamp>.json
```

### File Exfiltration

The C2 server copies files **before** they are encrypted (clean copies). This simulates real ransomware data theft.

---

## Advanced Features

### Phase 1: Utilities (ransomware/utils.py)

**Functions**:

| Function | Purpose |
|----------|---------|
| `run_cmd(cmd)` | Execute shell commands |
| `is_admin()` | Check administrator privileges |
| `is_vm()` | Detect VM/sandbox environment |
| `delay_if_sandbox()` | Add delays if VM detected |
| `delete_shadow_copies()` | Delete Windows shadow copies (anti-recovery) |
| `disable_services()` | Disable backup/security services |
| `generate_ransom_note()` | Create README.txt in encrypted directories |

**VM Detection Methods**:
- MAC address prefixes (VMware, VirtualBox, Hyper-V)
- VM-specific files (vmmouse.sys, vmhgfs.sys)
- CPU core count (< 3 cores = suspicious)
- RAM size (< 4GB = suspicious)
- Registry keys (VBoxGuest, VMTools)

---

### Phase 2: Persistence (ransomware/persistence.py)

**Functions**:

| Function | Description |
|----------|-------------|
| `check_mutex(mutex_name)` | Prevent multiple instances |
| `install_run_key(exe_path)` | Add to HKCU\\...\\Run registry |
| `install_startup_shortcut(exe_path)` | Create startup folder shortcut |
| `install_scheduled_task(exe_path)` | Create Windows scheduled task |
| `anti_vm_abort()` | Abort if VM detected |
| `timing_check_abort()` | Abort if running too fast (debugger) |

---

### Phase 3: Spread (ransomware/spread.py)

**Functions**:

| Function | Description |
|----------|-------------|
| `enumerate_network_shares()` | Find SMB shares via `net view` |
| `enumerate_unc_paths()` | Find mounted network drives |
| `spread_to_share(share_path, exe_path)` | Copy ransomware to share |
| `spread_to_network(exe_path)` | Spread to all accessible shares |
| `harvest_credentials_from_registry()` | Read stored credentials |
| `harvest_wifi_passwords()` | Extract WiFi passwords via netsh |
| `enumerate_smb_ports()` | Scan for SMB (445) on local subnet |

---

### Phase 5: Stealth (ransomware/stealth.py)

**Functions**:

| Function | Description |
|----------|-------------|
| `indirect_syscall(...)` | Execute syscalls indirectly (anti-hook) |
| `disable_defender()` | Disable Windows Defender |
| `clear_event_logs()` | Clear Security/System/Application logs |
| `exclude_from_backup(path)` | Add path to backup exclusions |
| `hide_process()` | Hide from debugger via NtSetInformationThread |
| `wipe_free_space(path)` | Overwrite free space with zeros |
| `uac_bypass()` | Bypass UAC via fodhelper.exe |

**Note**: These features are disabled by default via feature flags in `config.py`.

---

## Configuration

### Environment Variables (.env)

```ini
# Required
C2_SERVER_URL=http://127.0.0.1:8080
ENCRYPTION_KEY_PATH=./encryption.key
RSA_PRIVATE_KEY_PATH=c2_private_key.pem

# Optional
LOG_LEVEL=INFO
PAYMENT_ADDRESS=1BitcoinEaterAddressDontSendf59kuE

# Feature flags
ENABLE_UTILS=true
ENABLE_PERSISTENCE=false
ENABLE_SPREAD=false
ENABLE_C2_TLS=false
ENABLE_STEALTH=false
```

### RSA Key Generation

```bash
python generate_keys.py
```

Creates:
- `c2_private_key.pem`: Server private key (KEEP SECURE)
- `c2_public_key.pem`: Server public key

---

## Testing

### Test Suite

```bash
# Run all tests
pytest

# Run specific test
pytest tests/test_discovery.py

# Run GUI tests (requires pytest-qt)
pytest tests/test_gui.py -v
```

### Test Files

| File | Coverage |
|------|----------|
| `test_discovery.py` | File discovery with temp files |
| `test_encryptor.py` | Placeholder for encryption tests |
| `test_network.py` | Network error handling |
| `test_gui.py` | GUI visibility tests |

### Manual Testing

```bash
# 1. Generate keys
python generate_keys.py

# 2. Start C2 server (terminal 1)
python c2_server/c2_server_alt.py

# 3. Run encryption (terminal 2)
python main.py -p "./testDir/banking_receipts" -e

# 4. In GUI, enter code: bitcoin

# 5. Check darkSecureFolder/ for exfiltrated files
# 6. Check c2_data/ for machine data
```

---

## Security Considerations

### For Researchers

1. **Isolated Environment**: Always run in VM/disconnected network
2. **Test Data Only**: Never use on production/real data
3. **Key Management**: C2 private key must be kept secure
4. **Cleanup**: Use `clean_dark_secure_folder.py` to remove exfiltrated data

### Defensive Indicators

| Indicator | Detection Method |
|-----------|------------------|
| File extension `.wasted` | File monitoring |
| HTTP POST to `/exfiltrate` | Network monitoring |
| Registry Run key modifications | Registry monitoring |
| Shadow copy deletion | Event log analysis |
| Rapid file modification | EDR behavioral analysis |

### Mitigations

| Technique | Mitigation |
|-----------|------------|
| Hybrid Encryption | Network segmentation, backup encryption |
| File Discovery | Principle of least privilege |
| C2 Communication | DNS filtering, egress rules |
| Persistence | Registry monitoring, EDR |
| Shadow Copy Deletion | Offline backups, VSS monitoring |

---

## API Reference

### Exceptions (ransomware/exceptions.py)

```python
class RansomwareError(Exception): pass
class NetworkError(RansomwareError): pass
class EncryptionError(RansomwareError): pass
class DiscoveryError(RansomwareError): pass
```

### Logging

Uses `loguru` for structured logging:

```python
from ransomware.logging import logger
logger.info("Message")
logger.error("Error: {e}", e=exception)
```

---

## Docker Usage

```bash
# Build image
docker build -t ransomware-poc .

# Run with X11 forwarding (Linux)
docker run -e DISPLAY=$DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix ransomware-poc
```

---

## License & Legal Notice

**For educational and ethical research use only.**

- Do not use on production or unauthorized systems
- Authors are not responsible for misuse or damage
- Always comply with local laws and regulations

---

## Contact

- Email: mudityadev@gmail.com
- Repository: https://github.com/Mudityadev/PainPain-Ransomware-PoC
- YouTube Demo: [Watch Video](https://youtu.be/0KRUst9dbDk)

---

> "Cybersecurity is not about avoiding threats — it's about understanding them first."
