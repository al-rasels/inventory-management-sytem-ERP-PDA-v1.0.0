import logging
import os
from logging.handlers import RotatingFileHandler
from src.core.config import LOG_DIR

def setup_logger(name: str):
    """Sets up a structured logger with file and console handlers."""
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Prevent duplicate handlers
    if not logger.handlers:
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

        # File Handler (Rotating)
        file_handler = RotatingFileHandler(
            os.path.join(LOG_DIR, "sun_erp.log"),
            maxBytes=5*1024*1024,  # 5MB
            backupCount=5
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Console Handler
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    return logger

# Global app logger
app_logger = setup_logger("SUN_ERP")
