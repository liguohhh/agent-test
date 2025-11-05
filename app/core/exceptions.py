"""
自定义异常类

定义应用中使用的各种自定义异常
"""

from typing import Any, Dict, Optional


class APIError(Exception):
    """API基础异常类"""

    def __init__(
        self,
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_code = error_code
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "error": self.__class__.__name__,
            "message": self.message,
            "status_code": self.status_code,
            "error_code": self.error_code,
            "details": self.details
        }


class ValidationError(APIError):
    """数据验证错误"""

    def __init__(self, message: str, field: Optional[str] = None, **kwargs):
        super().__init__(message, status_code=400, **kwargs)
        self.field = field


class FunctionNotFoundError(APIError):
    """功能未找到错误"""

    def __init__(self, function_id: str, **kwargs):
        message = f"功能ID '{function_id}' 不存在或已禁用"
        super().__init__(message, status_code=404, error_code="FUNCTION_NOT_FOUND", **kwargs)
        self.function_id = function_id


class DeepSeekAPIError(APIError):
    """DeepSeek API调用错误"""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, status_code=502, error_code="DEEPSEEK_API_ERROR", **kwargs)


class DeepSeekTimeoutError(APIError):
    """DeepSeek API超时错误"""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, status_code=408, error_code="DEEPSEEK_TIMEOUT", **kwargs)


class StreamError(APIError):
    """流式响应错误"""

    def __init__(self, message: str, stream_id: Optional[str] = None, **kwargs):
        super().__init__(message, status_code=500, error_code="STREAM_ERROR", **kwargs)
        self.stream_id = stream_id


class CacheError(APIError):
    """缓存操作错误"""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, status_code=500, error_code="CACHE_ERROR", **kwargs)


class DatabaseError(APIError):
    """数据库操作错误"""

    def __init__(self, message: str, **kwargs):
        super().__init__(message, status_code=500, error_code="DATABASE_ERROR", **kwargs)