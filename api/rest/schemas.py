"""Modelos Pydantic para API HTTP"""

from pydantic import BaseModel, Field, EmailStr
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
    refresh_token: Optional[str] = None  # Opcional, pois principal está no cookie HttpOnly
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
    is_active: bool
    balance: float

    class Config:
        from_attributes = True


class ChangePassword(BaseModel):
    """Modelo para troca de senha"""
    old_password: str
    new_password: str = Field(..., min_length=8, max_length=100)
