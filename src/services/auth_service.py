import hashlib
import pandas as pd
from typing import Optional
from src.core.exceptions import AuthenticationError, DuplicateError, ValidationError
from src.services.types import AuthResult
from src.core.safety import SafetyManager, AuditLogger
from src.utils.validators import Validator
from src.utils.logger import app_logger

class AuthService:
    """User authentication and authorization service."""
    
    def __init__(self, user_repo):
        self.repo = user_repo
        
    def login(self, username: str, password: str) -> AuthResult:
        """Authenticate user."""
        if not username or not password:
            raise ValidationError("Username and password required")
            
        hashed_pw = self._hash_password(password)
        user = self.repo.authenticate(username, hashed_pw)
        
        if not user:
            AuditLogger.log_action(username, "LOGIN_FAIL", "Invalid credentials")
            raise AuthenticationError("Invalid username or password")
            
        AuditLogger.log_action(username, "LOGIN_SUCCESS", f"Role: {user['role']}")
        return AuthResult(success=True, user=user)

    @SafetyManager.transactional
    def create_user(self, username: str, full_name: str, password: str, role: str):
        """Create new user with validation and transaction safety."""
        Validator.validate_password_strength(password)
        
        app_logger.info(f"Creating user: {username} (Role: {role})")
        if self.repo.get_by_id(username):
            raise DuplicateError("User", "username", username)
            
        hashed_pw = self._hash_password(password)
        self.repo.create({
            "username": username,
            "full_name": full_name,
            "password_hash": hashed_pw,
            "role": role
        })
        
        AuditLogger.log_action("ADMIN", "USER_CREATE", f"Username: {username}, Role: {role}")
        return True

    @SafetyManager.transactional
    def change_password(self, username: str, old_password: str, new_password: str):
        """Change user password with verification and transaction safety."""
        Validator.validate_password_strength(new_password)
        
        app_logger.info(f"Changing password for user: {username}")
        # Verify old password
        self.login(username, old_password)
        
        hashed_pw = self._hash_password(new_password)
        self.repo.update(username, {"password_hash": hashed_pw})
        
        AuditLogger.log_action(username, "PASSWORD_CHANGE", "Success")
        return True

    def delete_user(self, username: str) -> bool:
        """Delete a user. Prevents deleting the 'admin' account."""
        if username == "admin":
            raise ValidationError("username", "Cannot delete the master admin account")
            
        app_logger.warning(f"Deleting user: {username}")
        self.repo.delete(username)
        AuditLogger.log_action("ADMIN", "USER_DELETE", f"Username: {username}")
        return True

    def list_users(self) -> pd.DataFrame:
        """List all users."""
        return self.repo.get_all()

    def _hash_password(self, password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
