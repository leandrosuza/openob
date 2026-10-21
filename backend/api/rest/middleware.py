"""Middleware para verificação de subscriptions e segurança"""

from fastapi import HTTPException, Depends, Request
from datetime import datetime, timezone
from typing import Optional, Callable
from functools import wraps
from api.rest.security import get_current_user
from models.user import User
from repositories.repository_factory import RepositoryFactory
from config.settings import Settings
from core.logger import LoggerConfig, get_logger

logger = get_logger(__name__)
security_logger = LoggerConfig.get_security_logger()


async def check_ownership(user_id_field: str = "user_id"):
    """Middleware para verificar se o usuário é dono do recurso"""
    async def dependency(request: Request, current_user: User = Depends(get_current_user)):
        resource_user_id = request.path_params.get(user_id_field)
        if resource_user_id and int(resource_user_id) != current_user.id:
            security_logger.warning(f"Tentativa de acesso não autorizado: user={current_user.id}, recurso={request.url.path}")
            raise HTTPException(status_code=403, detail="Acesso não autorizado")
        return current_user
    return dependency


async def check_subscription(required_plan_type: Optional[str] = None):
    """Middleware para verificar se o usuário tem o plano requerido"""
    async def dependency(current_user: User = Depends(get_current_user)):
        if not current_user.current_subscription_id:
            if required_plan_type and required_plan_type != "free":
                raise HTTPException(status_code=403, detail="Plano gratuito não tem acesso a este recurso")
            return current_user
        
        try:
            config = Settings.to_dict()
            subscription_repo = RepositoryFactory.create_subscription_repository(config)
            subscription = await subscription_repo.get_by_id(current_user.current_subscription_id)
            await subscription_repo.close()
            
            if not subscription:
                raise HTTPException(status_code=403, detail="Subscription não encontrada")
            
            if subscription.status != "active":
                raise HTTPException(status_code=403, detail="Subscription não está ativa")
            
            if subscription.end_date < datetime.now(timezone.utc):
                await subscription_repo.update_status(subscription.id, "grace_period")
                await subscription_repo.close()
                logger.warning(f"Subscription expirou: user={current_user.id}, subscription_id={subscription.id}")
                # Ainda permite acesso se estiver em grace period
                return current_user
            
            return current_user
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao verificar subscription: {e}")
            raise HTTPException(status_code=500, detail="Erro ao verificar subscription")
    
    return dependency


async def check_expiration():
    """Middleware para bloquear acesso se subscription expirou (fora de grace period)"""
    async def dependency(current_user: User = Depends(get_current_user)):
        if not current_user.current_subscription_id:
            return current_user
        
        try:
            config = Settings.to_dict()
            subscription_repo = RepositoryFactory.create_subscription_repository(config)
            subscription = await subscription_repo.get_by_id(current_user.current_subscription_id)
            await subscription_repo.close()
            
            if not subscription:
                return current_user
            
            if subscription.status == "expired":
                logger.warning(f"Acesso bloqueado: user={current_user.id} plano expirou")
                raise HTTPException(status_code=403, detail="Plano expirado. Renove para continuar.")
            
            if subscription.status == "cancelled":
                logger.warning(f"Acesso bloqueado: user={current_user.id} plano cancelado")
                raise HTTPException(status_code=403, detail="Plano cancelado.")
            
            return current_user
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Erro ao verificar expiração: {e}")
            raise HTTPException(status_code=500, detail="Erro ao verificar expiração")
    
    return dependency


async def check_grace_period():
    """Middleware para verificar se está em grace period"""
    async def dependency(current_user: User = Depends(get_current_user)):
        if not current_user.current_subscription_id:
            return current_user
        
        try:
            config = Settings.to_dict()
            subscription_repo = RepositoryFactory.create_subscription_repository(config)
            subscription = await subscription_repo.get_by_id(current_user.current_subscription_id)
            await subscription_repo.close()
            
            if not subscription:
                return current_user
            
            if subscription.status == "grace_period":
                logger.warning(f"User em grace period: user={current_user.id}, subscription expira em {subscription.end_date}")
                # Ainda permite acesso, mas avisa
                return current_user
            
            return current_user
        except Exception as e:
            logger.error(f"Erro ao verificar grace period: {e}")
            return current_user
    
    return dependency
