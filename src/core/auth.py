import hashlib
import sqlite3
from src.core.config import SQLITE_DB_PATH

class AuthManager:
    def __init__(self):
        self._init_auth_table()

    def _init_auth_table(self):
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                password_hash TEXT,
                role TEXT,
                full_name TEXT
            )
        ''')
        # Add default admin if not exists
        cursor.execute("SELECT * FROM users WHERE username='admin'")
        if not cursor.fetchone():
            pw_hash = hashlib.sha256("admin123".encode()).hexdigest()
            cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)", 
                         ('admin', pw_hash, 'Admin', 'System Administrator'))
        conn.commit()
        conn.close()

    def login(self, username, password):
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        cursor.execute("SELECT * FROM users WHERE username=? AND password_hash=?", (username, pw_hash))
        user = cursor.fetchone()
        conn.close()
        
        if user:
            return {"username": user[0], "role": user[2], "full_name": user[3]}
        return None

    def create_user(self, username, password, role, full_name):
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        pw_hash = hashlib.sha256(password.encode()).hexdigest()
        try:
            cursor.execute("INSERT INTO users VALUES (?, ?, ?, ?)", (username, pw_hash, role, full_name))
            conn.commit()
            return True
        except:
            return False
        finally:
            conn.close()

    def change_password(self, username, old_password, new_password):
        """Change password after verifying the old one."""
        if not self.login(username, old_password):
            return False, "Current password is incorrect"
        
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        new_hash = hashlib.sha256(new_password.encode()).hexdigest()
        cursor.execute("UPDATE users SET password_hash = ? WHERE username = ?", (new_hash, username))
        conn.commit()
        conn.close()
        return True, "Password changed successfully"

    def delete_user(self, username):
        """Delete a user (cannot delete 'admin')."""
        if username == 'admin':
            return False, "Cannot delete the admin account"
        conn = sqlite3.connect(SQLITE_DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        conn.commit()
        conn.close()
        return True, f"User '{username}' deleted"

