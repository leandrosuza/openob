"""
Trading models with Pydantic validation
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator
from enum import Enum
import uuid


class OrderDirection(str, Enum):
    """Direção da ordem"""
    CALL = "call"
    PUT = "put"


class OrderStatus(str, Enum):
    """Status da ordem"""
    PENDING = "pending"
    OPEN = "open"
    WIN = "win"
    LOSS = "loss"
    TIMEOUT = "timeout"
    CLOSED = "closed"


class OrderResult(BaseModel):
    """Resultado de uma ordem"""
    order_id: str
    status: OrderStatus
    profit: float = 0
    message: str = ""

    class Config:
        frozen = True


class Order(BaseModel):
    """Modelo de ordem para validação"""
    asset: str
    amount: float
    direction: OrderDirection
    duration: int
    request_id: Optional[str] = Field(default_factory=lambda: str(uuid.uuid4()))

    @field_validator("amount")
    @classmethod
    def amount_must_be_positive(cls, v):
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v

    @field_validator("duration")
    @classmethod
    def duration_must_be_valid(cls, v):
        if v < 5:
            raise ValueError("Duration must be at least 5 seconds")
        return v
