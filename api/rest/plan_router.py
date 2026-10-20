"""Router para planos"""

from fastapi import APIRouter, HTTPException
from api.rest.schemas import PlanResponse
from repositories.repository_factory import RepositoryFactory
from config.settings import Settings
from core.logger import get_logger

router = APIRouter(prefix="/plans", tags=["plans"])
logger = get_logger(__name__)


@router.get("", response_model=list[PlanResponse])
async def list_plans():
    """Listar todos os planos disponíveis"""
    try:
        config = Settings.to_dict()
        plan_repo = RepositoryFactory.create_plan_repository(config)
        plans = await plan_repo.get_active_plans()
        await plan_repo.close()
        return plans
    except Exception as e:
        logger.error(f"Erro ao listar planos: {e}")
        raise HTTPException(status_code=500, detail="Erro ao listar planos")


@router.get("/{plan_id}", response_model=PlanResponse)
async def get_plan(plan_id: int):
    """Obter detalhes de um plano específico"""
    try:
        config = Settings.to_dict()
        plan_repo = RepositoryFactory.create_plan_repository(config)
        plan = await plan_repo.get_by_id(plan_id)
        await plan_repo.close()
        
        if not plan:
            raise HTTPException(status_code=404, detail="Plano não encontrado")
        
        return plan
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao buscar plano: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar plano")
