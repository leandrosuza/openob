"""Router de autenticação HTTP com JWT

Este módulo implementa endpoints de autenticação HTTP para usuários,
usando JWT e refresh tokens em cookies HttpOnly.

Separado de api/auth.py que é autenticação WebSocket com PocketOption.

Endpoints (v1):
- POST /v1/auth/register - Registro de usuário
- POST /v1/auth/login - Login (retorna access token + refresh token em cookie)
- POST /v1/auth/refresh - Renovar access token com refresh token
- GET /v1/auth/me - Obter usuário atual
- POST /v1/auth/change-password - Trocar senha
- POST /v1/auth/logout - Logout

Segurança:
- Logs de segurança dedicados (logs/auth.txt)
- Rate limiting
- Validação de entradas
- Ocultação de dados sensíveis
- Invalidação de tokens no logout
"""

from fastapi import APIRouter, HTTPException, status, Depends, Response, Cookie, Request
from fastapi.security import OAuth2PasswordRequestForm
from datetime import timedelta
from typing import Optional
import logging

from models.user import User
from repositories.repository_factory import RepositoryFactory
from repositories.sqlite.sqlite_user_repository import SQLiteUserRepository
from config.settings import Settings
from api.rest.security import (
    create_access_token,
    create_refresh_token,
    verify_token,
    ACCESS_TOKEN_EXPIRE_MINUTES,
    REFRESH_TOKEN_EXPIRE_DAYS,
    oauth2_scheme
)
from api.rest.schemas import UserRegister, UserLogin, Token, UserResponse, ChangePassword
from core.logger import get_logger
from slowapi import Limiter
from slowapi.util import get_remote_address


logger = get_logger(__name__)
security_logger = logging.getLogger("security")
limiter = Limiter(key_func=get_remote_address)
router = APIRouter(prefix="/auth", tags=["Authentication"])


# Blacklist simples de tokens (em produção, usar Redis)
token_blacklist = set()


# Rate limits configuráveis via ENV
RATE_LIMIT_REGISTER = Settings.RATE_LIMIT_REGISTER
RATE_LIMIT_LOGIN = Settings.RATE_LIMIT_LOGIN
RATE_LIMIT_REFRESH = Settings.RATE_LIMIT_REFRESH


def get_user_repository():
    """Dependency para obter repositório de usuários"""
    config = Settings.to_dict()
    return RepositoryFactory.create_user_repository(config)


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    user_repo = Depends(get_user_repository)
) -> User:
    """Obter usuário atual a partir do token JWT"""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = verify_token(token, "access")
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except HTTPException:
        raise credentials_exception
    
    user = await user_repo.get_by_username(username)
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo"
        )
    
    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(RATE_LIMIT_REGISTER)  # Rate limit configurável via ENV
async def register(
    user_data: UserRegister,
    request: Request,
    user_repo = Depends(get_user_repository)
):
    """Registrar novo usuário"""
    # Log de segurança
    security_logger.info(f"Registro tentado: username={user_data.username}, email={user_data.email}, ip={request.client.host if request.client else 'unknown'}")
    
    # Verificar se username já existe
    existing_user = await user_repo.get_by_username(user_data.username)
    if existing_user:
        security_logger.warning(f"Falha registro: username já existe - {user_data.username}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome de usuário já existe"
        )
    
    # Verificar se email já existe
    existing_email = await user_repo.get_by_email(user_data.email)
    if existing_email:
        security_logger.warning(f"Falha registro: email já existe - {user_data.email}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email já cadastrado"
        )
    
    # Hash da senha
    password_hash = SQLiteUserRepository.hash_password(user_data.password)
    
    # Criar usuário
    user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=password_hash,
        ssid_demo=user_data.ssid_demo,
        ssid_real=user_data.ssid_real,
        plan_id=None,
        is_active=True,
        balance=0.0
    )
    
    created_user = await user_repo.create(user)
    logger.info(f"Usuário registrado: {created_user.username}")
    security_logger.info(f"Registro sucesso: username={created_user.username}, id={created_user.id}")
    
    return UserResponse(
        id=created_user.id,
        username=created_user.username,
        email=created_user.email,
        plan_id=created_user.plan_id,
        is_active=created_user.is_active,
        balance=created_user.balance
    )


@router.post("/login", response_model=Token)
@limiter.limit(RATE_LIMIT_LOGIN)  # Rate limit configurável via ENV
async def login(
    response: Response,
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    user_repo = Depends(get_user_repository)
):
    """Login de usuário"""
    # Log de segurança (sem senha)
    security_logger.info(f"Login tentado: username={form_data.username}, ip={request.client.host if request.client else 'unknown'}")
    
    # Buscar usuário
    user = await user_repo.get_by_username(form_data.username)
    if not user:
        security_logger.warning(f"Falha login: usuário não encontrado - {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar senha
    is_valid = await user_repo.verify_password(form_data.username, form_data.password)
    if not is_valid:
        security_logger.warning(f"Falha login: senha incorreta - {form_data.username}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        security_logger.warning(f"Falha login: usuário inativo - {form_data.username}")
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
    
    # Salvar refresh token em cookie HttpOnly (proteção contra XSS)
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,  # Proteção contra XSS
        secure=False,  # False para testes locais, True em produção
        samesite="lax",  # Proteção CSRF
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # 7 dias em segundos
    )
    
    logger.info(f"Usuário logado: {user.username}")
    security_logger.info(f"Login sucesso: username={user.username}, id={user.id}")
    
    # Retornar apenas access token (refresh token está no cookie HttpOnly)
    return Token(
        access_token=access_token
    )


@router.post("/refresh", response_model=Token)
@limiter.limit(RATE_LIMIT_REFRESH)  # Rate limit configurável via ENV
async def refresh_token(
    request: Request,
    response: Response,
    user_repo = Depends(get_user_repository)
):
    """Renovar token de acesso usando refresh token do cookie HttpOnly"""
    # Obter refresh token do cookie HttpOnly
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        security_logger.warning(f"Falha refresh: token não encontrado, ip={request.client.host if request.client else 'unknown'}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token não encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verificar se token está na blacklist
    if refresh_token in token_blacklist:
        security_logger.warning(f"Falha refresh: token na blacklist, ip={request.client.host if request.client else 'unknown'}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido"
        )
    
    # Decodificar refresh token
    try:
        payload = verify_token(refresh_token, "refresh")
        username: str = payload.get("sub")
        user_id: int = payload.get("user_id")
        if username is None or user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token inválido"
            )
    except HTTPException:
        security_logger.warning(f"Falha refresh: token inválido, ip={request.client.host if request.client else 'unknown'}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token inválido ou expirado"
        )
    
    # Verificar se usuário existe
    user = await user_repo.get_by_id(user_id)
    if not user or not user.is_active:
        security_logger.warning(f"Falha refresh: usuário inválido/inativo - user_id={user_id}")
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
    
    # Criar novo refresh token (rotation - proteção contra reuso)
    new_refresh_token = create_refresh_token(
        data={"sub": user.username, "user_id": user.id}
    )
    
    # Adicionar antigo refresh token à blacklist
    token_blacklist.add(refresh_token)
    
    # Atualizar cookie com novo refresh token
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,  # Proteção contra XSS
        secure=False,  # False para testes locais, True em produção
        samesite="lax",  # Proteção CSRF
        max_age=REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60  # 7 dias em segundos
    )
    
    logger.info(f"Token renovado para: {user.username}")
    security_logger.info(f"Refresh sucesso: username={user.username}")
    
    # Retornar apenas access token (refresh token está no cookie HttpOnly)
    return Token(
        access_token=access_token
    )


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    """Obter informações do usuário atual"""
    return UserResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        plan_id=current_user.plan_id,
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
async def logout(
    response: Response,
    request: Request,
    current_user: User = Depends(get_current_user)
):
    """Logout do usuário - Invalida refresh token"""
    # Log de segurança
    security_logger.info(f"Logout: username={current_user.username}, id={current_user.id}, ip={request.client.host if request.client else 'unknown'}")
    
    # Adicionar refresh token à blacklist
    refresh_token = request.cookies.get("refresh_token")
    if refresh_token:
        token_blacklist.add(refresh_token)
        security_logger.info(f"Refresh token invalidado: user_id={current_user.id}")
    
    # Remover cookie
    response.delete_cookie(key="refresh_token")
    logger.info(f"Usuário fez logout: {current_user.username}")
    security_logger.info(f"Logout sucesso: username={current_user.username}")
    
    return {"message": "Logout realizado com sucesso"}
