"""User Model"""

from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from typing import Optional


class User(BaseModel):
    """Modelo de usuário"""
    
    id: Optional[int] = None
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=100)
    ssid: str = Field(..., min_length=10)
    plan_id: Optional[int] = None
    is_active: bool = True
    balance: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    
    class Config:
        frozen = True
