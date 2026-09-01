# encoding: UTF-8
from fastapi import APIRouter, Request
from app.core.response import api_success, api_failure
from app.core.security import create_token, create_refresh_token, validate_refresh_token, revoke_refresh_token, get_current_user_id
from app.api.controller.userController import UserController

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login")
async def auth_login(request: Request):
    """登录（白名单，无需认证）"""
    req_json = await request.json()
    controller = UserController(req_json)
    try:
        ret, err_msg = controller.login()
        if err_msg:
            return api_failure(40011, msg=err_msg)
        return api_success(data=ret)
    except Exception as e:
        return api_failure(40011, msg='数据库连接失败，请稍后重试！')
    finally:
        controller.close_session()


@router.post("/register")
async def auth_register(request: Request):
    """注册（白名单，无需认证）"""
    req_json = await request.json()
    controller = UserController(req_json)
    try:
        create_id, err_msg = controller.register()
        if err_msg:
            return api_failure(40009, msg=err_msg)
        return api_success(data={'id': create_id})
    finally:
        controller.close_session()


@router.post("/refresh")
async def auth_refresh(request: Request):
    """刷新 token（白名单，无需认证）"""
    req_json = await request.json()
    refresh_token = req_json.get('refreshToken') or req_json.get('refresh_token')
    access_token = req_json.get('accessToken') or req_json.get('access_token')

    if refresh_token:
        user_id = validate_refresh_token(refresh_token)
        if user_id:
            revoke_refresh_token(refresh_token)
            new_token, expire_seconds = create_token(user_id)
            new_refresh_token, refresh_expire_seconds = create_refresh_token(user_id)
            return api_success(data={
                'token': new_token,
                'token_type': 'Bearer',
                'expires_in': expire_seconds,
                'refresh_token': new_refresh_token,
                'refresh_expires_in': refresh_expire_seconds
            })
        return api_failure(40001, msg='refresh_token无效或已过期')

    elif access_token:
        user_id = get_current_user_id(access_token)
        if user_id:
            new_token, expire_seconds = create_token(user_id)
            return api_success(data={
                'token': new_token,
                'token_type': 'Bearer',
                'expires_in': expire_seconds
            })
        return api_failure(451, msg='access_token无效或已过期')

    return api_failure(40003, msg='请提供refresh_token或access_token')
