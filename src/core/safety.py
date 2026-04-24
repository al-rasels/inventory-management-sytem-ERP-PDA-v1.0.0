import os
import shutil
import logging
import functools
from datetime import datetime
from src.core.config import EXCEL_DB_PATH, BACKUP_DIR, LOG_DIR

# Setup Logging
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "system.log"),
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

class SafetyManager:
    @staticmethod
    def create_backup():
        """Creates a timestamped backup of the primary Excel database."""
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_ERP_{timestamp}.xlsx"
        backup_path = os.path.join(BACKUP_DIR, filename)
        
        try:
            shutil.copy2(EXCEL_DB_PATH, backup_path)
            logging.info(f"Backup created: {filename}")
            return backup_path
        except Exception as e:
            logging.error(f"Backup failed: {str(e)}")
            return None

    @staticmethod
    def rollback(backup_path):
        """Restores the Excel database from a backup."""
        if not backup_path or not os.path.exists(backup_path):
            return False
        try:
            shutil.copy2(backup_path, EXCEL_DB_PATH)
            logging.warning(f"Rollback performed using {backup_path}")
            return True
        except Exception as e:
            logging.error(f"Rollback failed: {str(e)}")
            return False

    @staticmethod
    def transactional(func):
        """Decorator to ensure atomicity via backup/rollback."""
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            backup_path = SafetyManager.create_backup()
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                logging.error(f"Transaction failed in {func.__name__}: {str(e)}")
                if backup_path:
                    SafetyManager.rollback(backup_path)
                raise e
        return wrapper

class CloudBackup:
    """Interface for Cloud Backups (Google Drive/S3)."""
    @staticmethod
    def sync_to_cloud(file_path):
        # Placeholder for future cloud integration
        logging.info(f"Cloud sync started for {file_path}")
        # Logic for API upload goes here
        pass

class AuditLogger:
    @staticmethod
    def log_action(user, action, details):
        logging.info(f"USER: {user} | ACTION: {action} | DETAILS: {details}")
        # Also write to SQLite audit_logs table via DatabaseEngine if needed
