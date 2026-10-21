"""Subscription Model"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class Subscription(BaseModel):
    """Modelo de subscription"""

    id: Optional[int] = None
    user_id: int = Field(..., gt=0)
    plan_id: int = Field(..., gt=0)
    start_date: datetime
    end_date: datetime
    status: str = Field(..., min_length=1, max_length=20)
    payment_method: Optional[str] = Field(None, max_length=50)
    payment_id: Optional[str] = Field(None, max_length=100)
    auto_renew: bool = False
    created_at: Optional[datetime] = None
    cancelled_at: Optional[datetime] = None
    expired_at: Optional[datetime] = None

    class Config:
        frozen = True
