"""
Authentication Service - User management and JWT tokens
"""

import os
import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict
from jose import JWTError, jwt
from dotenv import load_dotenv

load_dotenv()


class AuthService:
    """Handle user authentication and JWT token management."""
    
    # In-memory user storage (replace with database in production)
    users_db: Dict[str, Dict] = {}
    
    def __init__(self):
        """Initialize auth service."""
        self.secret_key = os.getenv("JWT_SECRET_KEY", secrets.token_urlsafe(32))
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 60 * 24 * 7  # 7 days
    
    def hash_password(self, password: str) -> str:
        """Hash password using SHA-256."""
        return hashlib.sha256(password.encode()).hexdigest()
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify password against hash."""
        return self.hash_password(plain_password) == hashed_password
    
    def create_user(self, email: str, password: str, full_name: str) -> Optional[Dict]:
        """
        Create a new user.
        
        Returns:
            User dict if successful, None if email already exists
        """
        if email in self.users_db:
            return None
        
        user_id = f"user_{secrets.token_hex(8)}"
        user = {
            "user_id": user_id,
            "email": email,
            "password_hash": self.hash_password(password),
            "full_name": full_name,
            "created_at": datetime.utcnow().isoformat()
        }
        
        self.users_db[email] = user
        return {
            "user_id": user_id,
            "email": email,
            "full_name": full_name,
            "created_at": user["created_at"]
        }
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict]:
        """
        Authenticate user with email and password.
        
        Returns:
            User dict if successful, None if authentication fails
        """
        user = self.users_db.get(email)
        if not user:
            return None
        
        if not self.verify_password(password, user["password_hash"]):
            return None
        
        return {
            "user_id": user["user_id"],
            "email": user["email"],
            "full_name": user["full_name"]
        }
    
    def create_access_token(self, user_id: str, email: str) -> str:
        """
        Create JWT access token.
        
        Args:
            user_id: User's unique identifier
            email: User's email
            
        Returns:
            JWT token string
        """
        expires_delta = timedelta(minutes=self.access_token_expire_minutes)
        expire = datetime.utcnow() + expires_delta
        
        to_encode = {
            "sub": user_id,
            "email": email,
            "exp": expire
        }
        
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[Dict]:
        """
        Verify JWT token and extract payload.
        
        Args:
            token: JWT token string
            
        Returns:
            Payload dict if valid, None if invalid
        """
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: str = payload.get("sub")
            email: str = payload.get("email")
            
            if user_id is None or email is None:
                return None
            
            return {"user_id": user_id, "email": email}
        except JWTError:
            return None


# Global auth service instance
auth_service = AuthService()
