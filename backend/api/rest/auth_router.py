"""Router de autenticação"""

from fastapi import APIRouter, HTTPException, status, Depends, Response, Cookie, Request
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta, datetime, timezone
from typing import Optional

from models.user import User
from repositories.repository_factory import RepositoryFactory
from config.settings import Settings
from api.rest.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    oauth2_scheme,
    get_current_user,
    get_user_repository
)
from api.rest.schemas import UserRegister, UserLogin, Token, UserResponse, ChangePassword
from core.logger import get_logger
from core.logger import LoggerConfig


logger = get_logger(__name__)
subscription_logger = LoggerConfig.get_subscription_logger()
router = APIRouter(prefix="/api/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserRegister,
    user_repo = Depends(get_user_repository)
):
    """Registrar novo usuário"""
    # Verificar se username já existe
    existing_user = await user_repo.get_by_username(user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome de usuário já existe"
        )

    # Verificar se email já existe
    existing_email = await user_repo.get_by_email(user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado"
        )

    # Hash da senha
    password_hash = await user_repo.hash_password(user_data.password)

    # Criar usuário com SSID placeholder (será configurado depois)
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=password_hash,
        ssid_demo="PLACEHOLDER_SSID",  # Será configurado depois
        ssid_real=None,
        plan_id=None,
        current_subscription_id=None,
        plan_expires_at=None,
        is_active=True,
        balance=0.0,
        mode="demo",
        is_connected=False,
        connection_status="disconnected",
        disconnect_reason=None
    )

    created_user = await user_repo.create(user)
    logger.info(f"Usuário registrado: {created_user.username}")

    # Criar subscription free automaticamente
    config = Settings.to_dict()
    subscription_repo = RepositoryFactory.create_subscription_repository(config)
    plan_repo = RepositoryFactory.create_plan_repository(config)

    # Obter plano free
    free_plan = await plan_repo.get_by_type("free")

    if free_plan:
        # Criar subscription free
        start_date = datetime.now(timezone.utc)
        # Free não expira - usar data muito distante no futuro
        from datetime import timedelta
        end_date = start_date + timedelta(days=365 * 100)  # 100 anos

        subscription = await subscription_repo.create_for_user(
            user_id=created_user.id,
            plan_id=free_plan.id,
            start_date=start_date,
            end_date=end_date,
            payment_method=None,
            payment_id=None,
            auto_renew=False
        )

        # Atualizar user com subscription_id
        created_user.current_subscription_id = subscription.id
        created_user.plan_expires_at = None
        await user_repo.update(created_user)

        subscription_logger.info(f"Subscription free criada para user {created_user.id}, subscription_id={subscription.id}")

    return UserResponse(
        id=created_user.id,
        username=created_user.username,
        email=created_user.email,
        plan_id=created_user.plan_id,
        current_subscription_id=created_user.current_subscription_id,
        plan_expires_at=created_user.plan_expires_at,
        is_active=created_user.is_active,
        balance=created_user.balance
    )


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_repo = Depends(get_user_repository)
):
    """Login de usuário"""
    # Buscar usuário
    user = await user_repo.get_by_username(form_data.username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verificar senha
    is_valid = await user_repo.verify_password(form_data.username, form_data.password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo"
        )

    # Criar tokens
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )
    refresh_token = create_refresh_token(
        data={"sub": user.username, "user_id": user.id}
    )

    logger.info(f"Usuário logado: {user.username}")

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
        user_id=user.id
    )


@router.post("/refresh", response_model=Token)
async def refresh_token(
    refresh_token: str,
    user_repo = Depends(get_user_repository)
):
    """Renovar token de acesso usando refresh token"""
    try:
        payload = verify_token(refresh_token, "refresh")
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido"
            )
    except HTTPException:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou expirado"
        )

    user = await user_repo.get_by_username(username)
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário inválido ou inativo"
        )

    # Criar novo access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username, "user_id": user.id},
        expires_delta=access_token_expires
    )

    logger.info(f"Token renovado para: {user.username}")

    return Token(
        access_token=access_token,
        refresh_token=refresh_token
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Obter informações do usuário atual"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        plan_id=current_user.plan_id,
        current_subscription_id=current_user.current_subscription_id,
        plan_expires_at=current_user.plan_expires_at,
        is_active=current_user.is_active,
        balance=current_user.balance
    )


@router.post("/change-password")
async def change_password(
    password_data: ChangePassword,
    current_user: User = Depends(get_current_user),
    user_repo = Depends(get_user_repository)
):
    """Trocar senha do usuário"""
    # Verificar senha atual
    is_valid = await user_repo.verify_password(current_user.username, password_data.old_password)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha atual incorreta"
        )

    # Atualizar senha
    await user_repo.update_password(current_user.id, password_data.new_password)
    logger.info(f"Senha alterada para usuário: {current_user.username}")

    return {"message": "Senha alterada com sucesso"}


@router.post("/logout")
async def logout(response: Response):
    """Logout do usuário"""
    # Em uma implementação completa, adicionaria o refresh token a uma blacklist
    # Por enquanto, apenas removemos os cookies do cliente
    response.delete_cookie(key="refresh_token")
    logger.info("Usuário fez logout")
    return {"message": "Logout realizado com sucesso"}
