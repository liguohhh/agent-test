"""
API响应模型

定义统一的API响应格式
"""

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel


class BaseResponse(BaseModel):
    """基础响应模型"""
    code: int = 200
    message: str = "success"


class SuccessResponse(BaseResponse):
    """成功响应模型"""
    code: int = 200
    message: str = "success"
    data: Optional[Dict[str, Any]] = None


class ErrorResponse(BaseResponse):
    """错误响应模型"""
    code: int
    message: str
    error_code: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class FunctionInfoResponse(BaseModel):
    """功能信息响应模型"""
    id: str
    name: str
    description: str
    input_schema: Dict[str, Any]
    max_input_length: Optional[int] = None
    estimated_time: Optional[float] = None
    supports_stream: bool = True
    model_used: Optional[str] = None


class FunctionListResponse(BaseResponse):
    """功能列表响应模型"""
    code: int = 200
    message: str = "success"
    data: List[FunctionInfoResponse]


class ExecuteRequest(BaseModel):
    """功能执行请求模型"""
    function_id: str
    input: Dict[str, Any]
    use_cache: bool = True
    model_name: Optional[str] = None


class ExecuteResponse(BaseModel):
    """功能执行响应模型"""
    function_id: str
    result: Dict[str, Any]
    usage: Dict[str, Any]
    execution_time: float
    model_used: str
    cached: bool = False


class StreamRequest(BaseModel):
    """流式执行请求模型"""
    function_id: str
    input: Dict[str, Any]
    stream_mode: str = "tokens"  # tokens/chunks/sentences


class HealthResponse(BaseModel):
    """健康检查响应模型"""
    status: str
    version: str
    timestamp: int
    services: Dict[str, str]