"""User Model"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class User(BaseModel):
    """Modelo de usuário"""

    id: Optional[int] = None
    username: str = Field(..., min_length=3, max_length=50)
    email: str = Field(..., min_length=5, max_length=100)
    password_hash: str = Field(..., min_length=60)
    ssid_demo: str = Field(..., min_length=10)
    ssid_real: Optional[str] = Field(None, min_length=10)
    plan_id: Optional[int] = None
    current_subscription_id: Optional[int] = None
    plan_expires_at: Optional[datetime] = None
    is_active: bool = True
    balance: float = 0.0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        frozen = True
