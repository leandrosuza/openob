"""Router para subscriptions"""

from fastapi import APIRouter, HTTPException, Depends
from datetime import datetime, timezone, timedelta
from api.rest.schemas import SubscriptionResponse, SubscriptionRequest
from repositories.repository_factory import RepositoryFactory
from config.settings import Settings
from core.logger import get_logger
from api.rest.security import get_current_user
from models.user import User

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])
logger = get_logger(__name__)


@router.get("/me", response_model=SubscriptionResponse)
async def get_my_subscription(current_user: User = Depends(get_current_user)):
    """Obter subscription atual do usuário"""
    try:
        config = Settings.to_dict()
        subscription_repo = RepositoryFactory.create_subscription_repository(config)
        subscription = await subscription_repo.get_active_by_user(current_user.id)
        await subscription_repo.close()
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Nenhuma subscription ativa encontrada")
        
        return subscription
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar subscription: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar subscription")


@router.get("/history", response_model=list[SubscriptionResponse])
async def get_subscription_history(current_user: User = Depends(get_current_user), limit: int = 100, offset: int = 0):
    """Obter histórico completo de subscriptions do usuário"""
    try:
        config = Settings.to_dict()
        subscription_repo = RepositoryFactory.create_subscription_repository(config)
        subscriptions = await subscription_repo.get_history(current_user.id, limit, offset)
        await subscription_repo.close()
        return subscriptions
    except Exception as e:
        logger.error(f"Erro ao buscar histórico: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar histórico")


@router.get("/{subscription_id}", response_model=SubscriptionResponse)
async def get_subscription(subscription_id: int, current_user: User = Depends(get_current_user)):
    """Obter detalhes de uma subscription específica"""
    try:
        config = Settings.to_dict()
        subscription_repo = RepositoryFactory.create_subscription_repository(config)
        subscription = await subscription_repo.get_by_id(subscription_id)
        await subscription_repo.close()
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Subscription não encontrada")
        
        if subscription.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Acesso não autorizado")
        
        return subscription
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar subscription: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar subscription")


@router.post("/cancel")
async def cancel_subscription(current_user: User = Depends(get_current_user)):
    """Cancelar subscription atual do usuário"""
    try:
        config = Settings.to_dict()
        subscription_repo = RepositoryFactory.create_subscription_repository(config)
        subscription = await subscription_repo.get_active_by_user(current_user.id)
        
        if not subscription:
            raise HTTPException(status_code=404, detail="Nenhuma subscription ativa encontrada")
        
        await subscription_repo.cancel(subscription.id)
        await subscription_repo.close()
        
        logger.info(f"Subscription cancelada: user={current_user.id}, subscription_id={subscription.id}")
        return {"message": "Subscription cancelada com sucesso"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao cancelar subscription: {e}")
        raise HTTPException(status_code=500, detail="Erro ao cancelar subscription")


@router.post("/manual-upgrade")
async def manual_upgrade(request: SubscriptionRequest, current_user: User = Depends(get_current_user)):
    """Upgrade manual de plano (apenas para testes/admin)"""
    try:
        config = Settings.to_dict()
        plan_repo = RepositoryFactory.create_plan_repository(config)
        subscription_repo = RepositoryFactory.create_subscription_repository(config)
        
        plan = await plan_repo.get_by_id(request.plan_id)
        await plan_repo.close()
        
        if not plan:
            raise HTTPException(status_code=404, detail="Plano não encontrado")
        
        duration_days = request.duration_days_override if request.duration_days_override else plan.duration_days
        start_date = datetime.now(timezone.utc)
        end_date = start_date + timedelta(days=duration_days)
        
        subscription = await subscription_repo.create_for_user(
            user_id=current_user.id,
            plan_id=plan.id,
            start_date=start_date,
            end_date=end_date,
            payment_method="manual",
            payment_id="manual",
            auto_renew=False
        )
        await subscription_repo.close()
        
        logger.info(f"Upgrade manual: user={current_user.id}, plano={plan.name}, subscription_id={subscription.id}")
        return subscription
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao fazer upgrade manual: {e}")
        raise HTTPException(status_code=500, detail="Erro ao fazer upgrade manual")
