from src.repositories.base_repository import BaseRepository
from typing import List, Any, Optional
from datetime import datetime
import pandas as pd

class AuditRepository(BaseRepository):
    """Handles data access for audit logs."""
    
    def get_all(self) -> pd.DataFrame:
        return self.db.execute_query("SELECT * FROM audit_logs ORDER BY timestamp DESC")

    def get_by_id(self, log_id: int) -> Optional[dict]:
        df = self.db.execute_query("SELECT * FROM audit_logs WHERE id = ?", (log_id,))
        return df.iloc[0].to_dict() if not df.empty else None

    def create(self, data: dict) -> bool:
        query = "INSERT INTO audit_logs (user, action, details, timestamp) VALUES (?, ?, ?, ?)"
        params = (data['user'], data['action'], data['details'], data['timestamp'])
        self.db.execute_write(query, params)
        return True

    def update(self, log_id: int, data: dict) -> bool:
        # Audit logs should never be updated
        return False

    def delete(self, log_id: int) -> bool:
        # Audit logs should never be deleted via repo
        return False

    def log(self, user: str, action: str, details: str):
        """Helper to quickly log an action."""
        self.create({
            "user": user,
            "action": action,
            "details": details,
            "timestamp": datetime.now().isoformat()
        })
