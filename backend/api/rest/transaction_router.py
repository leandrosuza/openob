"""Router para transações"""

from fastapi import APIRouter, HTTPException, Depends
from api.rest.schemas import TransactionResponse
from repositories.repository_factory import RepositoryFactory
from config.settings import Settings
from core.logger import get_logger
from api.rest.security import get_current_user
from models.user import User

router = APIRouter(prefix="/transactions", tags=["transactions"])
logger = get_logger(__name__)


@router.get("/me", response_model=list[TransactionResponse])
async def get_my_transactions(current_user: User = Depends(get_current_user), limit: int = 100, offset: int = 0):
    """Obter histórico de transações do usuário"""
    try:
        config = Settings.to_dict()
        transaction_repo = RepositoryFactory.create_transaction_repository(config)
        transactions = await transaction_repo.get_user_transactions(current_user.id, limit, offset)
        await transaction_repo.close()
        return transactions
    except Exception as e:
        logger.error(f"Erro ao buscar transações: {e}")
        raise HTTPException(status_code=500, detail="Erro ao buscar transações")


@router.post("/webhook")
async def payment_webhook(payload: dict):
    """Webhook para gateway de pagamento (Stripe, MercadoPago, etc.)"""
    # TODO: Implementar validação de HMAC signature
    # TODO: Implementar proteção contra replay attacks
    # TODO: Processar payment e criar subscription
    
    logger.info(f"Webhook recebido: payload={payload}")
    return {"message": "Webhook recebido (não implementado ainda)"}
