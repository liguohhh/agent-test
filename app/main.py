"""
FastAPI应用主入口

创建和配置FastAPI应用实例，设置中间件和路由
"""

import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.api import api_router
from app.config import settings
from app.database import init_database
from app.core.exceptions import APIError

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动时执行
    logger.info("正在启动AI应用后端接口...")

    # 初始化数据库
    try:
        init_database()
        logger.info("数据库初始化完成")
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        raise

    # 验证DeepSeek API连接
    try:
        from app.services import FunctionManager
        function_manager = FunctionManager()
        connection_result = function_manager.validate_connection()
        if connection_result["status"] == "success":
            logger.info("DeepSeek API连接验证成功")
        else:
            logger.warning(f"DeepSeek API连接验证失败: {connection_result.get('error')}")
    except Exception as e:
        logger.warning(f"DeepSeek API连接验证异常: {e}")

    logger.info("应用启动完成")

    yield

    # 关闭时执行
    logger.info("正在关闭应用...")


# 创建FastAPI应用实例
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="基于Python FastAPI框架实现的小型AI应用后端接口，集成DeepSeek大语言模型",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加受信任主机中间件
if not settings.debug:
    app.add_middleware(
        TrustedHostMiddleware,
        allowed_hosts=["*"]  # 生产环境中应该配置具体的主机
    )


# 请求处理时间中间件
@app.middleware("http")
async def add_process_time_header(request: Request, call_next):
    """添加请求处理时间头"""
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    response.headers["X-Process-Time"] = str(process_time)
    return response


# 全局异常处理器
@app.exception_handler(APIError)
async def api_exception_handler(request: Request, exc: APIError):
    """处理自定义API异常"""
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """处理未捕获的通用异常"""
    logger.error(f"未处理的异常: {type(exc).__name__}: {str(exc)}", exc_info=True)

    return JSONResponse(
        status_code=500,
        content={
            "code": 500,
            "message": "服务器内部错误",
            "error": type(exc).__name__,
            "details": str(exc) if settings.debug else None
        }
    )


# 注册路由
app.include_router(
    api_router,
    prefix=settings.api_prefix,
    tags=["AI功能API"]
)


# 根路径
@app.get("/", summary="根路径", description="应用基本信息")
async def root():
    """根路径端点"""
    return {
        "name": settings.app_name,
        "version": settings.app_version,
        "description": "基于FastAPI和DeepSeek的AI应用后端接口",
        "docs_url": "/docs" if settings.debug else None,
        "api_prefix": settings.api_prefix
    }


# 健康检查端点（简化版）
@app.get("/ping", summary="Ping检查", description="简单的健康检查")
async def ping():
    """Ping检查端点"""
    return {
        "status": "ok",
        "timestamp": int(time.time()),
        "version": settings.app_version
    }


# 开发环境下的调试端点
if settings.debug:
    @app.get("/debug/config", summary="配置信息", description="显示当前配置（仅开发环境）")
    async def debug_config():
        """调试配置信息端点"""
        return {
            "app_name": settings.app_name,
            "app_version": settings.app_version,
            "debug": settings.debug,
            "api_prefix": settings.api_prefix,
            "database_url": settings.database_url,
            "deepseek_base_url": settings.deepseek_base_url,
            "deepseek_model": settings.deepseek_model,
            "enable_cache": settings.enable_cache,
            "cache_ttl": settings.cache_ttl,
            "log_level": settings.log_level
        }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )