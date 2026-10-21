"""Autotrade Config Model"""

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Dict, Any, Optional


class AutotradeConfig(BaseModel):
    """Modelo de configuração de autotrade"""

    id: Optional[int] = None
    user_id: int = Field(..., description="ID do usuário")
    strategy_name: str = Field(..., min_length=1, max_length=100, description="Nome da estratégia")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parâmetros da estratégia")
    amount: float = Field(default=5.0, gt=0, description="Valor padrão para trades")
    is_active: bool = Field(default=True, description="Se a estratégia está ativa")
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        frozen = True
