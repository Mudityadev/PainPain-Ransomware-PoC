# PainPain Ransomware PoC

## 1. Overview

📺 **Watch the Demo Video:**  
[![Watch on YouTube](https://img.youtube.com/vi/0KRUst9dbDk/0.jpg)](https://youtu.be/0KRUst9dbDk?si=xA-qgz5TpnEX_twe)

**PainPain** is a modular, educational Proof-of-Concept (PoC) ransomware project. It demonstrates file discovery, encryption, exfiltration, and a realistic GUI, all for research and ethical hacking education. **Do not use for malicious purposes.**
---

## 2. Key Features
- **Recursive File Discovery** (configurable)
- **AES Encryption/Decryption** with Fernet
- **C2 Server Simulation** (Flask, HTTP POST)
- **Modern GUI** (Tkinter, realistic ransom note, timer, payment instructions)
- **Professional Logging** (console & file)
- **Safe PoC** (test directories, no destructive defaults)
- **Extensible, Modular Python Package**
- **Unit & Integration Tests**

---

## 3. Quick Start

### Installation
```sh
pip install -r requirements.txt
```

### Environment Setup
- Copy `.env.example` to `.env` and fill in your secrets/keys/configuration.
- **Never commit your `.env` file!**

### Running the C2 Server
```sh
python c2_server/c2_server_alt.py
```

### Running the Agent (CLI & GUI)
- **Encrypt files:**
  ```sh
  python main.py -p "./testDir/banking_receipts" -e
  ```
- **Decrypt files:**
  ```sh
  python main.py -p "./testDir/banking_receipts" -d
  ```
- **GUI:**
  - The GUI will display a ransom note, timer, and payment instructions.
  - Enter the code `bitcoin` and click **Decrypt Files**. After successful decryption, the window closes automatically in 1 second.

---

## 4. Project Structure

```
PainPain-Ransomware-PoC/
├── main.py                # Main CLI entry point
├── ransomware/            # Core package
│   ├── core.py            # Orchestrates discovery, encryption, GUI
│   ├── config.py          # AppConfig (pydantic)
│   ├── gui/               # GUI logic (Tkinter)
│   ├── gui_main.py        # Main GUI entry point
│   ├── crypto/            # Encryption, key management
│   ├── discovery/         # File discovery logic
│   ├── network/           # C2 client logic
│   ├── exceptions.py      # Custom exceptions
│   └── ...
├── c2_server/             # C2 server (Flask)
│   ├── c2_server_alt.py   # HTTP POST C2 server
│   └── ...
├── testDir/               # Sample/test data
├── tests/                 # Unit/integration tests
├── requirements.txt       # Python dependencies
├── Dockerfile             # Containerization
├── README.md              # Documentation
└── ...
```

---

## 5. Module Documentation

### CLI/Agent (`main.py`)
- Entry point for encryption/decryption.
- Uses argparse for CLI options.
- Loads config from `.env` via `AppConfig`.
- Calls `RansomwareApp` for all operations.

### Core Logic (`ransomware/core.py`)
- `RansomwareApp`: Orchestrates key management, file discovery, encryption/decryption, C2 exfiltration, and GUI launch.

### GUI (`ransomware/gui/main.py`, `ransomware/gui_main.py`)
- Tkinter-based GUI simulating a real ransomware note.
- Timer, payment instructions, and decryption workflow.
- Window closes 1 second after successful decryption.

### Crypto (`ransomware/crypto/`)
- `encryptor.py`: Fernet-based file encryption/decryption.
- `keys.py`: Key load/save utilities.

### Discovery (`ransomware/discovery/`)
- `discoverer.py`: Recursively finds files, with optional extension filtering.

### Network (`ransomware/network/`)
- `client.py`: Sends exfiltration data to C2 server via HTTP POST.

### C2 Server (`c2_server/c2_server_alt.py`)
- Flask app, receives exfiltration data at `/exfiltrate`.
- Logs all events, stores machine data and exfiltrated files.

### Tests (`tests/`)
- Unit and integration tests for discovery, encryption, GUI, and network.

### Sample Data (`testDir/`)
- Contains realistic test files (docs, images, configs, etc.) for safe demonstration.

---

## 6. Configuration
- All config is managed via `.env` and `ransomware/config.py`.
- Example `.env`:
  ```ini
  c2_server_url="http://localhost:8080"
  encryption_key_path="./encryption.key"
  log_level="INFO"
  environment="development"
  timeout=30
  hardcoded_key="your_hardcoded_key_here"
  decrypt_code="bitcoin"
  server_public_rsa_key="-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"
  server_private_rsa_key="-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----"
  extension=".wasted"
  host="127.0.0.1"
  port=8080
  payment_address="1BitcoinEaterAddressDontSendf59kuE"
  ```

---

## 7. Docker Usage

### Build the Docker Image
```sh
docker build -t ransomware-poc .
```

### Run with X11 Forwarding (for GUI)
- See README above for Linux, macOS, and Windows/WSL2 instructions.

---

## 8. Testing
- Run all tests:
  ```sh
  pytest
  ```
- Tests are in the `tests/` directory.

---

## 9. Contributing
- Fork the repo, create a feature branch, follow modular structure and docstring standards.
- Write clean code with type hints and docstrings.
- Submit a PR with a meaningful description.

---

## 10. Legal & Ethical Notice
- **For educational and ethical research use only.**
- Do not use on production or unauthorized systems.
- Authors are not responsible for misuse or damage.
- Always comply with local laws and regulations.

---

## 11. Contact
- Suggestions, security insights, or collaboration ideas? Email: mudityadev@gmail.com

---

> "Cybersecurity is not about avoiding threats — it's about understanding them first."
