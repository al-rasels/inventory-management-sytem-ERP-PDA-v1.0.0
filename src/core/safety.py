import os
import shutil
import logging
import functools
from datetime import datetime
from src.core.config import BACKUP_DIR, LOG_DIR, SQLITE_DB_PATH

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
        """Creates a timestamped backup of the SQLite database."""
        if not os.path.exists(BACKUP_DIR):
            os.makedirs(BACKUP_DIR)
        
        if not os.path.exists(SQLITE_DB_PATH):
            logging.warning("No database file to back up.")
            return None

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"backup_ERP_{timestamp}.db"
        backup_path = os.path.join(BACKUP_DIR, filename)
        
        try:
            shutil.copy2(SQLITE_DB_PATH, backup_path)
            logging.info(f"Backup created: {filename}")
            return backup_path
        except Exception as e:
            logging.error(f"Backup failed: {str(e)}")
            return None

    @staticmethod
    def rollback(backup_path):
        """Restores the database from a backup."""
        if not backup_path or not os.path.exists(backup_path):
            return False
        try:
            shutil.copy2(backup_path, SQLITE_DB_PATH)
            logging.warning(f"Rollback performed using {backup_path}")
            return True
        except Exception as e:
            logging.error(f"Rollback failed: {str(e)}")
            return False

    @staticmethod
    def transactional(func):
        """Decorator for service-layer transaction safety.
        
        Uses try/except with logging. For critical operations,
        a pre-operation backup can be triggered manually.
        This avoids creating a file backup on every single write.
        """
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                logging.error(f"Transaction failed in {func.__name__}: {str(e)}")
                raise
        return wrapper


class AuditLogger:
    """Writes audit entries to both file log and SQLite."""
    
    _db = None
    
    @classmethod
    def set_db(cls, db_engine):
        """Set the database engine for SQLite audit logging."""
        cls._db = db_engine
    
    @staticmethod
    def log_action(user, action, details):
        logging.info(f"AUDIT | USER: {user} | ACTION: {action} | DETAILS: {details}")
        if AuditLogger._db:
            try:
                AuditLogger._db.execute_write(
                    "INSERT INTO audit_logs (user, action, details) VALUES (?, ?, ?)",
                    (user, action, details)
                )
            except Exception:
                pass  # Don't let audit logging crash the app
