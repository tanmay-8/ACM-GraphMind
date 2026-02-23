"""
Authentication Models for GraphMind API
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserSignup(BaseModel):
    """User signup request model."""
    email: EmailStr
    password: str = Field(..., min_length=6, description="Password must be at least 6 characters")
    full_name: str = Field(..., min_length=1, description="User's full name")


class UserLogin(BaseModel):
    """User login request model."""
    email: EmailStr
    password: str


class Token(BaseModel):
    """JWT token response model."""
    access_token: str
    token_type: str = "bearer"
    user_id: str
    email: str
    full_name: str


class UserResponse(BaseModel):
    """User information response model."""
    user_id: str
    email: str
    full_name: str
    created_at: Optional[str] = None
