"""Gerenciador de subscriptions - verificação periódica de expiração"""

import asyncio
from datetime import datetime, timezone, timedelta
from repositories.repository_factory import RepositoryFactory
from repositories.sqlite.sqlite_user_repository import SQLiteUserRepository
from config.settings import Settings
from core.logger import LoggerConfig, get_logger

logger = get_logger(__name__)
subscription_logger = LoggerConfig.get_subscription_logger()


class SubscriptionManager:
    """Gerenciador de subscriptions"""

    def __init__(self):
        self.config = Settings.to_dict()
        self.check_interval_hours = Settings.SUBSCRIPTION_CHECK_INTERVAL_HOURS
        self.grace_period_days = Settings.GRACE_PERIOD_DAYS
        self.running = False

    async def check_and_expire_subscriptions(self):
        """Verificar e expirar subscriptions"""
        try:
            logger.info(f"Iniciando verificação de subscriptions (check_interval={self.check_interval_hours}h)")
            
            subscription_repo = RepositoryFactory.create_subscription_repository(self.config)
            user_repo = RepositoryFactory.create_user_repository(self.config)
            
            total_verified = 0
            grace_count = 0
            expired_count = 0
            renew_count = 0
            
            # 1. Mover expirados para grace period
            expired_subs = await subscription_repo.get_expired_subscriptions()
            total_verified += len(expired_subs)
            
            for sub in expired_subs:
                await subscription_repo.update_status(sub.id, "grace_period")
                subscription_logger.warning(f"Subscription {sub.id} entrou em grace period: user={sub.user_id}, expires_em={sub.end_date}, grace_ends={sub.end_date + timedelta(days=self.grace_period_days)}")
                grace_count += 1
            
            # 2. Mover grace period para expired (downgrade)
            grace_subs = await subscription_repo.get_grace_period_subscriptions(self.grace_period_days)
            total_verified += len(grace_subs)
            
            for sub in grace_subs:
                await subscription_repo.expire_subscription(sub.id)
                
                # Atualizar user para voltar para free
                await user_repo.update(
                    type(sub)('', username='', email='', password_hash='', ssid_demo='', 
                          current_subscription_id=None, plan_expires_at=None, id=sub.user_id)
                )
                
                subscription_logger.warning(f"Subscription {sub.id} expirou: user={sub.user_id} voltou para FREE, grace period terminou em {sub.end_date + timedelta(days=self.grace_period_days)}")
                expired_count += 1
            
            # 3. Verificar auto-renew (futuro)
            renew_subs = await subscription_repo.get_auto_renew_expiring()
            total_verified += len(renew_subs)
            
            for sub in renew_subs:
                # TODO: Criar transaction pendente para cobrança
                subscription_logger.info(f"Subscription {sub.id} marcada para renovação automática: user={sub.user_id}")
                renew_count += 1
            
            logger.info(f"Verificação concluída: verificados={total_verified}, grace_period={grace_count}, expirados={expired_count}, auto_renew={renew_count}")
            
        except Exception as e:
            logger.error(f"Erro na verificação de subscriptions: {e}")
            subscription_logger.error(f"Erro na verificação de subscriptions: {e}")

    async def expiration_check_loop(self):
        """Loop periódico para verificar expiração"""
        self.running = True
        logger.info("Task de verificação de subscriptions iniciada")
        
        while self.running:
            await self.check_and_expire_subscriptions()
            await asyncio.sleep(self.check_interval_hours * 3600)  # Converter horas para segundos

    async def stop(self):
        """Parar o loop de verificação"""
        self.running = False
        logger.info("Task de verificação de subscriptions parada")

    async def check_expired_on_startup(self):
        """Verificar subscriptions expiradas ao iniciar o sistema"""
        try:
            logger.info("Verificando subscriptions expiradas no startup")
            subscription_repo = RepositoryFactory.create_subscription_repository(self.config)
            user_repo = RepositoryFactory.create_user_repository(self.config)
            
            expired_subs = await subscription_repo.get_expired_subscriptions()
            
            for sub in expired_subs:
                await subscription_repo.update_status(sub.id, "grace_period")
                subscription_logger.warning(f"Subscription {sub.id} entrou em grace period no startup: user={sub.user_id}")
            
            grace_subs = await subscription_repo.get_grace_period_subscriptions(self.grace_period_days)
            
            for sub in grace_subs:
                await subscription_repo.expire_subscription(sub.id)
                await user_repo.update(
                    type(sub)('', username='', email='', password_hash='', ssid_demo='', 
                          current_subscription_id=None, plan_expires_at=None, id=sub.user_id)
                )
                subscription_logger.warning(f"Subscription {sub.id} expirou no startup: user={sub.user_id} voltou para FREE")
            
            logger.info(f"Verificação no startup concluída: grace_period={len(expired_subs)}, expirados={len(grace_subs)}")
            
        except Exception as e:
            logger.error(f"Erro na verificação no startup: {e}")
            subscription_logger.error(f"Erro na verificação no startup: {e}")
