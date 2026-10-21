"""Plan Model"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class Plan(BaseModel):
    """Modelo de plano"""

    id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=50)
    type: str = Field(..., min_length=1, max_length=20)
    price: float = Field(..., ge=0)
    description: str = Field(..., min_length=1, max_length=500)
    duration_days: int = Field(..., ge=0)
    is_active: bool = True
    created_at: Optional[datetime] = None

    class Config:
        frozen = True
