# encoding: UTF-8
"""
FastAPI 安全依赖：认证与权限控制
"""
import json
import uuid
from typing import Optional, Tuple
from datetime import datetime, timedelta

import redis
from flask import g
from fastapi import Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.config import REDIS_URL

# Redis 客户端
redis_client = redis.from_url(REDIS_URL, decode_responses=True)

# Token 配置
TOKEN_PREFIX = 'effekt:token:'
TOKEN_CONTEXT_PREFIX = 'effekt:token:ctx:'
REFRESH_TOKEN_PREFIX = 'effekt:refresh:'
TOKEN_EXPIRE_SECONDS = 7200  # 2小时
REFRESH_TOKEN_EXPIRE_SECONDS = 86400 * 7  # 7天
TOKEN_REFRESH_THRESHOLD_SECONDS = 1800  # 30分钟

# 白名单路径（无需认证）
WHITELIST_PATHS = [
    '/health',
    '/docs',
    '/redoc',
    '/openapi.json',
    '/it/api/auth/login',
    '/it/api/auth/register',
    '/it/api/auth/refresh',
]

# HTTP Bearer 认证
security = HTTPBearer(auto_error=False)


def create_token(user_id: int) -> Tuple[str, int]:
    token = uuid.uuid4().hex
    redis_client.setex(f'{TOKEN_PREFIX}{token}', TOKEN_EXPIRE_SECONDS, str(user_id))
    return token, TOKEN_EXPIRE_SECONDS


def create_refresh_token(user_id: int) -> Tuple[str, int]:
    refresh_token = uuid.uuid4().hex
    redis_client.setex(f'{REFRESH_TOKEN_PREFIX}{refresh_token}', REFRESH_TOKEN_EXPIRE_SECONDS, str(user_id))
    return refresh_token, REFRESH_TOKEN_EXPIRE_SECONDS


def get_current_user_id(token: str) -> Optional[int]:
    """从 token 获取用户 ID"""
    user_id = redis_client.get(f'{TOKEN_PREFIX}{token}')
    return int(user_id) if user_id else None


def validate_refresh_token(refresh_token: str) -> Optional[int]:
    """验证 refresh token，返回 user_id"""
    key = f'{REFRESH_TOKEN_PREFIX}{refresh_token}'
    user_id = redis_client.get(key)
    if user_id:
        return int(user_id)
    return None


def revoke_refresh_token(refresh_token: str):
    """撤销 refresh token"""
    if refresh_token:
        redis_client.delete(f'{REFRESH_TOKEN_PREFIX}{refresh_token}')


def refresh_token_if_needed(token: str) -> int:
    """如果 token 即将过期，自动续期"""
    ttl = redis_client.ttl(f'{TOKEN_PREFIX}{token}')
    if ttl != -2 and ttl < TOKEN_REFRESH_THRESHOLD_SECONDS:
        redis_client.expire(f'{TOKEN_PREFIX}{token}', TOKEN_EXPIRE_SECONDS)
        return TOKEN_EXPIRE_SECONDS
    return ttl


def cache_token_context(token: str, user, role_ids: list, permission_codes: list):
    """缓存 token 上下文"""
    context = {
        'user': user.to_dict() if hasattr(user, 'to_dict') else user,
        'role_ids': role_ids,
        'permission_codes': permission_codes
    }
    redis_client.setex(
        f'{TOKEN_CONTEXT_PREFIX}{token}',
        TOKEN_REFRESH_THRESHOLD_SECONDS,
        json.dumps(context, default=str)
    )


def get_token_context(token: str) -> Optional[dict]:
    """获取缓存的 token 上下文"""
    context_str = redis_client.get(f'{TOKEN_CONTEXT_PREFIX}{token}')
    return json.loads(context_str) if context_str else None


def validate_refresh_token(refresh_token: str) -> Optional[int]:
    """验证刷新 token，返回 user_id 或 None"""
    key = f'{REFRESH_TOKEN_PREFIX}{refresh_token}'
    user_id = redis_client.get(key)
    return int(user_id) if user_id else None


def revoke_refresh_token(refresh_token: str):
    """撤销刷新 token"""
    if refresh_token:
        redis_client.delete(f'{REFRESH_TOKEN_PREFIX}{refresh_token}')


def revoke_all_refresh_tokens(user_id: int):
    """撤销某用户所有刷新 token"""
    keys = redis_client.keys(f'{REFRESH_TOKEN_PREFIX}*')
    for key in keys:
        stored_user_id = redis_client.get(key)
        if stored_user_id == str(user_id):
            redis_client.delete(key)


def logout_token(token: str):
    """登出，清除 token"""
    redis_client.delete(f'{TOKEN_PREFIX}{token}')
    redis_client.delete(f'{TOKEN_CONTEXT_PREFIX}{token}')


def _sync_legacy_flask_context(user_id: int, token: str, user, role_ids: list, permission_codes: list):
    """向仍使用 Flask g 的旧控制器同步当前认证用户。"""
    g.current_user_id = user_id
    g.current_user = user
    g.current_role_ids = role_ids
    g.current_permission_codes = permission_codes
    g.current_token = token


def has_permission(required_code: str, permission_codes: list) -> bool:
    """检查是否有权限"""
    if not required_code:
        return True
    if not permission_codes:
        return False
    if required_code in permission_codes:
        return True
    if '*:*' in permission_codes:
        return True
    if ':' in required_code:
        module_code = required_code.split(':', 1)[0]
        if f'{module_code}:*' in permission_codes:
            return True
        if '_' in module_code:
            parent_module_code = module_code.split('_', 1)[0]
            if f'{parent_module_code}:*' in permission_codes:
                return True
    return False


async def get_current_user(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db)
) -> Optional[dict]:
    """
    获取当前用户信息（FastAPI 依赖）
    
    用法:
        @router.get("/api/xxx")
        async def xxx(user: dict = Depends(get_current_user)):
            user_id = user['user_id']
    """
    # 检查白名单
    if request.url.path in WHITELIST_PATHS:
        return None
    
    # 提取 token
    token = None
    if credentials:
        token = credentials.credentials
    else:
        # 尝试从 header 中获取
        token = request.headers.get('accessToken') or request.headers.get('accesstoken')
    
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={'success': False, 'code': 40001, 'message': '缺少token！'},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 验证 token
    user_id = get_current_user_id(token)
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={'success': False, 'code': 451, 'message': 'token无效或已过期！'},
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # 尝试从缓存获取上下文
    token_context = get_token_context(token)
    if token_context:
        # 自动续期
        refresh_token_if_needed(token)
        _sync_legacy_flask_context(
            user_id,
            token,
            token_context.get('user', {}),
            token_context.get('role_ids', []),
            token_context.get('permission_codes', []),
        )
        return {**token_context, 'user_id': user_id, 'token': token}
    
    # 缓存未命中，从数据库查询
    from app.api.model.userModel import User
    from app.api.service.userService import UserService
    from app.api.service.rbacService import RbacService
    
    user = UserService.get_by_id(db, User, user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={'success': False, 'code': 40011, 'message': '未查询到对应用户！'},
        )
    
    role_ids = UserService.get_user_role_ids(db, user_id)
    permission_codes = RbacService.get_role_permission_codes(db, role_ids)
    
    # 缓存上下文
    cache_token_context(token, user, role_ids, permission_codes)
    
    # 自动续期
    refresh_token_if_needed(token)
    _sync_legacy_flask_context(user_id, token, user, role_ids, permission_codes)
    
    return {
        'user': user,
        'user_id': user_id,
        'role_ids': role_ids,
        'permission_codes': permission_codes,
        'token': token
    }


def require_permission(permission_code: str):
    """
    权限检查装饰器
    
    用法:
        @router.get("/api/xxx")
        async def xxx(user: dict = Depends(require_permission("project:list"))):
            ...
    """
    async def permission_checker(
        request: Request,
        credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
        db: Session = Depends(get_db)
    ) -> dict:
        user_info = await get_current_user(request, credentials, db)
        
        if user_info is None:
            # 白名单路径，直接放行
            return {}
        
        permission_codes = user_info.get('permission_codes', [])
        if not has_permission(permission_code, permission_codes):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={'success': False, 'code': 40003, 'message': '无权限访问该接口！'},
            )
        
        return user_info
    
    return permission_checker
