"""Transaction Model"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class Transaction(BaseModel):
    """Modelo de transação"""

    id: Optional[int] = None
    user_id: int = Field(..., gt=0)
    subscription_id: Optional[int] = Field(None, gt=0)
    plan_id: int = Field(..., gt=0)
    amount: float = Field(..., ge=0)
    currency: str = Field(..., min_length=3, max_length=3)
    status: str = Field(..., min_length=1, max_length=20)
    payment_method: str = Field(..., min_length=1, max_length=50)
    payment_id: Optional[str] = Field(None, max_length=100)
    created_at: Optional[datetime] = None

    class Config:
        frozen = True
