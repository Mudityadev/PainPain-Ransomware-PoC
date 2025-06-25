from loguru import logger
import sys
import os
from datetime import datetime

def init_logging(log_level: str = "INFO", log_dir: str = "logs"):
    """
    Initialize professional logging with loguru.
    Logs to both console and a timestamped file in the specified directory.
    """
    # Remove any existing handlers
    logger.remove()
    # Ensure log directory exists
    os.makedirs(log_dir, exist_ok=True)
    # Create log filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = os.path.join(log_dir, f"ransomware_{timestamp}.log")
    # Add file and console handlers
    logger.add(sys.stdout, level=log_level, format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{module}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>")
    logger.add(log_filename, level=log_level, format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {module}:{function}:{line} - {message}")
    logger.info(f"Logging initialized. Level: {log_level}, Log file: {log_filename}") 