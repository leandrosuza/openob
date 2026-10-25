"""Router para gerenciar configs de autotrade"""

import logging
from fastapi import APIRouter, HTTPException, Depends
from typing import List
from models.user import User
from models.autotrade import AutotradeConfig
from repositories.repository_factory import RepositoryFactory
from api.rest.security import get_current_user
from config.settings import Settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Autotrade"])


@router.post("/api/autotrade/configs")
async def create_autotrade_config(config: AutotradeConfig, current_user: User = Depends(get_current_user)):
    """Criar config de trading"""
    config.user_id = current_user.id

    config_dict = Settings.to_dict()
    autotrade_repo = RepositoryFactory.create_autotrade_repository(config_dict)

    # Verificar se já existe config para o usuário
    existing = await autotrade_repo.get_by_user(current_user.id)
    if existing:
        raise HTTPException(status_code=400, detail="Config já existe para este usuário")

    created = await autotrade_repo.create(config)
    return created


@router.get("/api/autotrade/configs/{user_id}")
async def get_autotrade_config(user_id: int, current_user: User = Depends(get_current_user)):
    """Obter config do usuário"""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Sem permissão")

    config_dict = Settings.to_dict()
    autotrade_repo = RepositoryFactory.create_autotrade_repository(config_dict)

    config = await autotrade_repo.get_by_user(user_id)
    if not config:
        raise HTTPException(status_code=404, detail="Config não encontrada")

    return config


@router.put("/api/autotrade/configs/{user_id}")
async def update_autotrade_config(user_id: int, config: AutotradeConfig, current_user: User = Depends(get_current_user)):
    """Atualizar config (auto-aplicado em tempo real)"""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Sem permissão")

    config.user_id = user_id
    config.id = config.id  # Mantém o ID existente

    config_dict = Settings.to_dict()
    autotrade_repo = RepositoryFactory.create_autotrade_repository(config_dict)

    updated = await autotrade_repo.update(config)
    return updated


@router.delete("/api/autotrade/configs/{user_id}")
async def delete_autotrade_config(user_id: int, current_user: User = Depends(get_current_user)):
    """Deletar config"""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Sem permissão")

    config_dict = Settings.to_dict()
    autotrade_repo = RepositoryFactory.create_autotrade_repository(config_dict)

    deleted = await autotrade_repo.delete(user_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Config não encontrada")

    return {"message": "Config deletada", "user_id": user_id}


@router.patch("/api/autotrade/configs/{user_id}/toggle")
async def toggle_autotrade_config(user_id: int, current_user: User = Depends(get_current_user)):
    """Alternar status is_active da config (iniciar/parar autotrade)"""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Sem permissão")

    config_dict = Settings.to_dict()
    autotrade_repo = RepositoryFactory.create_autotrade_repository(config_dict)

    config = await autotrade_repo.get_by_user(user_id)
    if not config:
        raise HTTPException(status_code=404, detail="Config não encontrada")

    # Alternar is_active
    updated_config = AutotradeConfig(
        id=config.id,
        user_id=config.user_id,
        strategy_name=config.strategy_name,
        parameters=config.parameters,
        amount=config.amount,
        is_active=not config.is_active,
        created_at=config.created_at,
        updated_at=config.updated_at
    )

    updated = await autotrade_repo.update(updated_config)
    return updated


@router.get("/api/autotrade/strategies")
async def list_strategies():
    """Listar estratégias disponíveis"""
    strategies = [
        {
            "name": "scalping5s",
            "description": "Estratégia de scalping de 5 segundos",
            "required_parameters": ["lookback_period", "ma_period", "rsi_period", "rsi_oversold", "rsi_overbought"]
        }
    ]
    return strategies


@router.get("/api/autotrade/strategies/{name}/parameters")
async def get_strategy_parameters(name: str):
    """Obter parâmetros necessários de uma estratégia"""
    from core.strategy.scalping5s import Scalping5sStrategy

    if name == "scalping5s":
        strategy = Scalping5sStrategy()
        return {
            "name": name,
            "required_parameters": strategy.get_required_parameters()
        }
    else:
        raise HTTPException(status_code=404, detail="Estratégia não encontrada")
