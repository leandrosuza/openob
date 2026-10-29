"""Router para gerenciar conexões de usuários"""

from fastapi import APIRouter, HTTPException, Depends, Body
from typing import List, Optional
from models.user import User
from repositories.repository_factory import RepositoryFactory
from api.rest.security import get_current_user
from config.settings import Settings
from pydantic import BaseModel

router = APIRouter(prefix="/users", tags=["User Connections"])


class SSIDUpdateRequest(BaseModel):
    """Modelo para atualização de SSID"""
    ssid_demo: Optional[str] = None
    ssid_real: Optional[str] = None


@router.post("/{user_id}/connect")
async def connect_user(user_id: int, current_user: User = Depends(get_current_user)):
    """Conectar usuário manualmente"""
    # Verificar se o usuário tem permissão (apenas próprio ou admin)
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Sem permissão")

    # Lógica de conexão será implementada via UserConnectionManager
    return {"message": "Solicitação de conexão enviada", "user_id": user_id}


@router.post("/{user_id}/disconnect")
async def disconnect_user(user_id: int, current_user: User = Depends(get_current_user)):
    """Desconectar usuário manualmente"""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Sem permissão")

    return {"message": "Solicitação de desconexão enviada", "user_id": user_id}


@router.get("/{user_id}/status")
async def get_user_status(user_id: int, current_user: User = Depends(get_current_user)):
    """Obter status da conexão do usuário"""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Sem permissão")

    config = Settings.to_dict()
    user_repo = RepositoryFactory.create_user_repository(config)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    return {
        "user_id": user_id,
        "is_connected": user.is_connected,
        "connection_status": user.connection_status,
        "mode": user.mode
    }


@router.get("/connections")
async def get_all_connections(current_user: User = Depends(get_current_user)):
    """Listar todas as conexões ativas"""
    # Implementar via UserConnectionManager
    return {"message": "Endpoint em desenvolvimento"}


@router.put("/{user_id}/mode")
async def update_user_mode(user_id: int, mode: str, current_user: User = Depends(get_current_user)):
    """Atualizar modo (demo/real) - dispara reconexão"""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Sem permissão")

    if mode not in ["demo", "real"]:
        raise HTTPException(status_code=400, detail="Modo inválido")

    config = Settings.to_dict()
    user_repo = RepositoryFactory.create_user_repository(config)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user.mode = mode
    await user_repo.update(user)

    return {"message": "Modo atualizado", "user_id": user_id, "mode": mode}


@router.put("/{user_id}/ssid")
async def update_user_ssid(
    user_id: int,
    request: SSIDUpdateRequest,
    current_user: User = Depends(get_current_user)
):
    """Atualizar SSID (demo e/ou real)"""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Sem permissão")

    config = Settings.to_dict()
    user_repo = RepositoryFactory.create_user_repository(config)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if request.ssid_demo is not None:
        user.ssid_demo = request.ssid_demo if request.ssid_demo else None
    if request.ssid_real is not None:
        user.ssid_real = request.ssid_real if request.ssid_real else None

    await user_repo.update(user)

    return {"message": "SSID atualizado", "user_id": user_id}


@router.put("/{user_id}/activate")
async def activate_user(user_id: int, current_user: User = Depends(get_current_user)):
    """Ativar usuário (is_active=True) - dispara conexão"""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Sem permissão")

    config = Settings.to_dict()
    user_repo = RepositoryFactory.create_user_repository(config)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user.is_active = True
    await user_repo.update(user)

    return {"message": "Usuário ativado", "user_id": user_id}


@router.put("/{user_id}/deactivate")
async def deactivate_user(user_id: int, current_user: User = Depends(get_current_user)):
    """Desativar usuário (is_active=False) - dispara desconexão"""
    if current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Sem permissão")

    config = Settings.to_dict()
    user_repo = RepositoryFactory.create_user_repository(config)
    user = await user_repo.get_by_id(user_id)

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    user.is_active = False
    await user_repo.update(user)

    return {"message": "Usuário desativado", "user_id": user_id}
