"""Market models with Pydantic validation"""




from typing import Optional
from pydantic import BaseModel, Field, field_validator, model_validator
from datetime import datetime




class Balance(BaseModel):
    """Informações de saldo com validação"""
    amount: float
    currency: str = "USD"
    is_demo: bool = True
    last_updated: datetime = Field(default_factory=datetime.now)




    @field_validator("amount")
    @classmethod
    def amount_must_be_valid(cls, v):
        if v < 0:
            raise ValueError("Balance cannot be negative")
        return v




    class Config:
        frozen = True




class Candle(BaseModel):
    """Candle de mercado com validação"""
    timestamp: datetime
    open: float
    close: float
    high: float
    low: float
    volume: Optional[float] = None
    asset: str
    timeframe: int




    @model_validator(mode="after")
    def validate_ohlc(self):
        """Validar que high >= low"""
        if self.high < self.low:
            raise ValueError("High must be greater than or equal to low")
        return self




    class Config:
        frozen = True
