# encoding: UTF-8
"""
用户模块 Pydantic Schema
统一使用 snake_case，前端传什么后端就接收什么。
"""
from pydantic import BaseModel, Field
from typing import Optional, List


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    username: str
    password: str
    real_name: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None
    created_by: Optional[int] = None


class UserCreateRequest(BaseModel):
    username: str
    password: str
    real_name: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None
    status: int = 1
    created_by: Optional[int] = None


class UserUpdateRequest(BaseModel):
    user_id: int
    username: Optional[str] = None
    real_name: Optional[str] = None
    password: Optional[str] = None
    mobile: Optional[str] = None
    email: Optional[str] = None
    avatar: Optional[str] = None
    status: Optional[int] = None


class UserListRequest(BaseModel):
    keyword: Optional[str] = None
    status: Optional[int] = None
    page_no: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=1000)


class TokenRefreshRequest(BaseModel):
    refresh_token: Optional[str] = None
    access_token: Optional[str] = None


class RoleAssignRequest(BaseModel):
    user_id: int
    role_ids: List[int] = []
