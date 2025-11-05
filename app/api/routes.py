"""
API路由定义

实现所有API端点
"""

from typing import Dict, Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app.api.responses import (
    ErrorResponse,
    ExecuteRequest,
    ExecuteResponse,
    FunctionListResponse,
    HealthResponse,
    StreamRequest
)
from app.services import FunctionManager
from app.utils.streaming import StreamingResponseManager, streaming_manager
from app.core.exceptions import APIError, ValidationError, FunctionNotFoundError
from app.config import settings

# 创建路由器
api_router = APIRouter()

# 依赖注入：获取功能管理器
def get_function_manager() -> FunctionManager:
    """获取功能管理器实例"""
    return FunctionManager()


@api_router.get(
    "/health",
    response_model=HealthResponse,
    summary="健康检查",
    description="检查应用和外部服务的健康状态"
)
async def health_check(
    function_manager: FunctionManager = Depends(get_function_manager)
) -> HealthResponse:
    """健康检查端点"""
    import time

    # 检查DeepSeek API连接
    deepseek_status = function_manager.validate_connection()
    services = {
        "deepseek_api": deepseek_status["status"],
        "database": "healthy",  # TODO: 实现数据库健康检查
        "cache": "enabled" if settings.enable_cache else "disabled"
    }

    overall_status = "healthy" if all(
        status == "healthy" or status == "enabled" or status == "success"
        for status in services.values()
    ) else "unhealthy"

    return HealthResponse(
        status=overall_status,
        version=settings.app_version,
        timestamp=int(time.time()),
        services=services
    )


@api_router.get(
    "/functions",
    response_model=FunctionListResponse,
    summary="获取功能列表",
    description="获取系统中所有可用的AI功能列表"
)
async def list_functions(
    function_manager: FunctionManager = Depends(get_function_manager)
) -> FunctionListResponse:
    """获取功能列表端点"""
    try:
        functions = function_manager.list_functions()
        return FunctionListResponse(data=functions)

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取功能列表失败: {str(e)}"
        )


@api_router.post(
    "/execute",
    response_model=ExecuteResponse,
    summary="同步执行功能",
    description="同步执行指定的AI功能，直接返回结果"
)
async def execute_function(
    request: ExecuteRequest,
    function_manager: FunctionManager = Depends(get_function_manager)
) -> ExecuteResponse:
    """同步执行功能端点"""
    try:
        result = function_manager.execute_function(
            function_id=request.function_id,
            input_data=request.input,
            model_name=request.model_name,
            use_cache=request.use_cache
        )

        return ExecuteResponse(**result)

    except FunctionNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行功能失败: {str(e)}")


@api_router.post(
    "/stream",
    summary="流式执行功能",
    description="流式执行AI功能，实时返回生成过程",
    responses={
        200: {
            "description": "Server-Sent Events流",
            "content": {
                "text/event-stream": {
                    "example": """data: {"type": "start", "function_id": "translation_zh_to_en", "timestamp": 1234567890}

data: {"type": "token", "content": "Hello", "timestamp": 1234567891}

data: {"type": "end", "usage": {"total_tokens": 10}, "execution_time": 2.5, "timestamp": 1234567893}"""
                }
            }
        }
    }
)
async def stream_execute_function(
    request: StreamRequest,
    function_manager: FunctionManager = Depends(get_function_manager)
) -> StreamingResponse:
    """流式执行功能端点"""
    try:
        # 生成流ID
        stream_id = streaming_manager.create_stream_id()

        # 注册流
        streaming_manager.register_stream(
            stream_id=stream_id,
            function_id=request.function_id
        )

        # 创建数据生成器
        data_generator = function_manager.stream_execute_function(
            function_id=request.function_id,
            input_data=request.input,
            use_cache=request.use_cache
        )

        # 返回SSE响应
        return streaming_manager.create_sse_response(
            stream_id=stream_id,
            data_generator=data_generator
        )

    except FunctionNotFoundError as e:
        return StreamingResponse(
            streaming_manager.create_error_stream(str(e)),
            media_type="text/event-stream"
        )
    except ValidationError as e:
        return StreamingResponse(
            streaming_manager.create_error_stream(str(e)),
            media_type="text/event-stream"
        )
    except Exception as e:
        return StreamingResponse(
            streaming_manager.create_error_stream(f"流式执行失败: {str(e)}"),
            media_type="text/event-stream"
        )


@api_router.get(
    "/stats",
    summary="获取统计信息",
    description="获取应用使用统计和性能数据"
)
async def get_stats(
    function_manager: FunctionManager = Depends(get_function_manager)
) -> Dict[str, Any]:
    """获取统计信息端点"""
    try:
        # 获取缓存统计
        from app.utils.cache import cache
        cache_stats = cache.get_stats()

        # 获取流式响应统计
        stream_stats = {
            "active_streams": streaming_manager.get_active_streams_count(),
            "max_concurrent_streams": streaming_manager.max_concurrent_streams
        }

        # TODO: 获取对话统计
        conversation_stats = {
            "total_conversations": 0,
            "avg_response_time": 0.0
        }

        return {
            "cache": cache_stats,
            "streaming": stream_stats,
            "conversations": conversation_stats,
            "functions": {
                "total_count": len(function_manager.list_functions()),
                "active_count": len(function_manager.list_functions())
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"获取统计信息失败: {str(e)}"
        )


@api_router.delete(
    "/cache",
    summary="清空缓存",
    description="清空所有缓存数据"
)
async def clear_cache() -> Dict[str, str]:
    """清空缓存端点"""
    try:
        from app.utils.cache import cache
        cache.clear()
        return {"message": "缓存已清空"}

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"清空缓存失败: {str(e)}"
        )


@api_router.delete(
    "/cache/{function_id}",
    summary="清空指定功能的缓存",
    description="清空指定功能的所有缓存数据"
)
async def clear_function_cache(function_id: str) -> Dict[str, Any]:
    """清空指定功能缓存端点"""
    try:
        from app.utils.cache import cache
        cleared_count = cache.clear_by_function(function_id)
        return {
            "message": f"功能 '{function_id}' 的缓存已清空",
            "cleared_count": cleared_count
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"清空功能缓存失败: {str(e)}"
        )