from src.repositories.base_repository import BaseRepository
from typing import List, Any, Optional
import pandas as pd

class UserRepository(BaseRepository):
    """Handles data access for users."""
    
    def get_all(self) -> pd.DataFrame:
        return self.db.execute_query("SELECT * FROM users")

    def get_by_id(self, username: str) -> Optional[dict]:
        df = self.db.execute_query("SELECT * FROM users WHERE username = ?", (username,))
        return df.iloc[0].to_dict() if not df.empty else None

    def create(self, data: dict) -> bool:
        query = "INSERT INTO users (username, full_name, password_hash, role) VALUES (?, ?, ?, ?)"
        params = (data['username'], data['full_name'], data['password_hash'], data['role'])
        self.db.execute_write(query, params)
        return True

    def update(self, username: str, data: dict) -> bool:
        # Only updating password_hash for now in this helper
        if 'password_hash' in data:
            self.db.execute_write("UPDATE users SET password_hash = ? WHERE username = ?", (data['password_hash'], username))
        return True

    def delete(self, username: str) -> bool:
        self.db.execute_write("DELETE FROM users WHERE username = ?", (username,))
        return True

    def authenticate(self, username: str, password_hash: str) -> Optional[dict]:
        query = "SELECT * FROM users WHERE username = ? AND password_hash = ?"
        df = self.db.execute_query(query, (username, password_hash))
        return df.iloc[0].to_dict() if not df.empty else None
