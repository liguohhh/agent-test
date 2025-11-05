"""
API路由定义

实现所有API端点
"""

from typing import Dict, Any
import time

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
    description="流式执行指定的AI功能，通过Server-Sent Events实时返回生成结果",
    response_class=StreamingResponse
)
async def stream_execute_function(
    request: StreamRequest,
    function_manager: FunctionManager = Depends(get_function_manager)
) -> StreamingResponse:
    """流式执行功能端点"""
    try:
        # 创建唯一的流ID
        stream_id = streaming_manager.create_stream_id()

        # 注册流
        streaming_manager.register_stream(
            stream_id=stream_id,
            function_id=request.function_id,
            client_info={
                "function_id": request.function_id,
                "stream_mode": request.stream_mode,
                "use_cache": request.use_cache,
                "user_agent": "client"  # 实际应用中可以从请求头获取
            }
        )

        # 创建数据生成器
        def generate_stream_data():
            try:
                # 使用功能管理器的流式执行方法
                for chunk in function_manager.stream_execute_function(
                    function_id=request.function_id,
                    input_data=request.input,
                    use_cache=request.use_cache
                ):
                    # 根据流模式过滤或转换数据
                    if request.stream_mode == "tokens":
                        # 逐token模式：直接传递token数据
                        if chunk["type"] in ["start", "token", "end", "error"]:
                            yield chunk
                    elif request.stream_mode == "chunks":
                        # 块模式：累积token到一定程度再发送
                        if chunk["type"] in ["start", "end", "error"]:
                            yield chunk
                        # chunk模式的token累积逻辑可以在客户端实现
                    elif request.stream_mode == "sentences":
                        # 句子模式：需要等待完整句子
                        if chunk["type"] in ["start", "end", "error"]:
                            yield chunk
                        # 句子模式的累积逻辑可以在客户端实现
                    else:
                        # 默认：传递所有数据
                        yield chunk

            except Exception as e:
                # 生成错误数据
                yield {
                    "type": "error",
                    "stream_id": stream_id,
                    "message": f"流式执行失败: {str(e)}",
                    "timestamp": int(time.time())
                }

        # 使用流式管理器创建SSE响应
        return streaming_manager.create_sse_response(
            stream_id=stream_id,
            data_generator=generate_stream_data()
        )

    except FunctionNotFoundError as e:
        # 返回错误流
        error_generator = streaming_manager.create_error_stream(str(e))
        return StreamingResponse(
            error_generator,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            }
        )
    except ValidationError as e:
        # 返回验证错误流
        error_generator = streaming_manager.create_error_stream(str(e))
        return StreamingResponse(
            error_generator,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            }
        )
    except Exception as e:
        # 返回通用错误流
        error_generator = streaming_manager.create_error_stream(f"服务器内部错误: {str(e)}")
        return StreamingResponse(
            error_generator,
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
            }
        )

