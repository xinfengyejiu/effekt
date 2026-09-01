# encoding: UTF-8
"""
FastAPI 依赖注入：统一响应格式
"""
from fastapi import Request
from fastapi.responses import JSONResponse
from typing import Optional, Any
from datetime import date, datetime
from decimal import Decimal


def json_serializer(obj):
    """JSON 序列化辅助函数"""
    if isinstance(obj, datetime):
        return obj.strftime('%Y-%m-%d %H:%M:%S')
    if isinstance(obj, date):
        return obj.strftime('%Y-%m-%d')
    if isinstance(obj, Decimal):
        return float(obj)
    raise TypeError(f"Type {type(obj)} not serializable")


def api_success(data: Optional[Any] = None, code: int = 20000, message: str = '') -> dict:
    """
    构建成功响应
    
    用法:
        return api_success(data=user_list)
        return api_success(data={'list': items, 'total': total})
    """
    return {
        'success': True,
        'code': code,
        'message': message,
        'data': data or {}
    }


def api_failure(code: int, msg: str = '', data: Optional[Any] = None) -> JSONResponse:
    """
    构建失败响应
    
    用法:
        return api_failure(40003, msg='参数有误')
    """
    from app.core.config import RES_CODE
    
    response_data = {
        'success': False,
        'code': code,
        'message': msg or RES_CODE.get(code, '未知错误'),
        'data': data or {}
    }
    return JSONResponse(content=response_data)


class ApiResponse:
    """
    兼容旧代码的 ApiResponse 类
    逐步迁移到 api_success / api_failure 函数
    """
    
    @staticmethod
    def build_success(code: int = 20000, message: str = '', data: Optional[Any] = None) -> dict:
        return api_success(data, code, message)
    
    @staticmethod
    def build_failure(code: int, msg: str = '', data: Optional[Any] = None) -> JSONResponse:
        return api_failure(code, msg, data)
