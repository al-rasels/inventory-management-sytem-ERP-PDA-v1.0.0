import os
import logging
import glob
from datetime import datetime
from src.core.config import BACKUP_DIR, MAX_BACKUP_FILES
from src.core.safety import SafetyManager
from src.utils.export_import import DataExporter, DataImporter

logger = logging.getLogger(__name__)

class BackupService:
    """Manages system backups, restores, and migrations."""
    
    def __init__(self, db):
        self.db = db

    def create_manual_backup(self):
        """Manually trigger a timestamped Excel backup."""
        return SafetyManager.create_backup()

    def get_backup_stats(self):
        """Get count and total size of backups."""
        files = glob.glob(os.path.join(BACKUP_DIR, "*.xlsx"))
        count = len(files)
        size_bytes = sum(os.path.getsize(f) for f in files)
        return count, size_bytes / (1024 * 1024)

    def cleanup_old_backups(self, keep=5):
        """Keep only the N most recent backups."""
        files = sorted(glob.glob(os.path.join(BACKUP_DIR, "*.xlsx")))
        if len(files) <= keep:
            return 0
        
        to_delete = files[:-keep]
        for f in to_delete:
            try:
                os.remove(f)
            except Exception as e:
                logger.error(f"Failed to delete backup {f}: {e}")
        
        return len(to_delete)

    def export_migration_zip(self):
        """Export full system for migration."""
        return DataExporter.export_full_system()

    def import_migration_zip(self, zip_path):
        """Import/Restore system from migration ZIP."""
        return DataImporter.import_full_system(zip_path, self.db)
