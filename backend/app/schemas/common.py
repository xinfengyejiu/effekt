# encoding: UTF-8
"""
通用 Pydantic Schema
"""
from pydantic import BaseModel, Field
from typing import Optional


class PageParams(BaseModel):
    """分页参数基类"""
    page_no: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=1000, description="每页数量")


class ApiResponseModel(BaseModel):
    """统一响应格式"""
    success: bool
    code: int
    message: str
    data: Optional[dict] = None
