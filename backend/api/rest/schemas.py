"""Modelos Pydantic para API HTTP"""

from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional


class UserRegister(BaseModel):
    """Modelo para registro de usuário"""
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=100)
    ssid_demo: str = Field(..., min_length=10)
    ssid_real: Optional[str] = Field(None, min_length=10)


class UserLogin(BaseModel):
    """Modelo para login de usuário"""
    username: str
    password: str


class Token(BaseModel):
    """Modelo para resposta de token"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Modelo para dados do token"""
    username: Optional[str] = None
    user_id: Optional[int] = None


class UserResponse(BaseModel):
    """Modelo para resposta de usuário"""
    id: int
    username: str
    email: str
    plan_id: Optional[int] = None
    current_subscription_id: Optional[int] = None
    plan_expires_at: Optional[datetime] = None
    is_active: bool
    balance: float

    class Config:
        from_attributes = True


class ChangePassword(BaseModel):
    """Modelo para troca de senha"""
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class PlanResponse(BaseModel):
    """Modelo para resposta de plano"""
    id: int
    name: str
    type: str
    price: float
    description: str
    duration_days: int
    is_active: bool

    class Config:
        from_attributes = True


class SubscriptionRequest(BaseModel):
    """Modelo para criação de subscription"""
    plan_id: int = Field(..., gt=0)
    duration_days_override: Optional[int] = Field(None, ge=0)


class SubscriptionResponse(BaseModel):
    """Modelo para resposta de subscription"""
    id: int
    user_id: int
    plan_id: int
    start_date: datetime
    end_date: datetime
    status: str
    payment_method: Optional[str] = None
    payment_id: Optional[str] = None
    auto_renew: bool
    created_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    expired_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TransactionResponse(BaseModel):
    """Modelo para resposta de transação"""
    id: int
    user_id: int
    subscription_id: Optional[int] = None
    plan_id: int
    amount: float
    currency: str
    status: str
    payment_method: str
    payment_id: Optional[str] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
