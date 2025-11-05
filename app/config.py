"""
应用配置模块

管理应用的所有配置参数，包括DeepSeek API配置、数据库配置、
日志配置等。
"""

from functools import lru_cache
from typing import Optional

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """应用配置类"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )

    # 应用基本配置
    app_name: str = "AI应用后端接口"
    app_version: str = "1.0.0"
    debug: bool = False
    host: str = "0.0.0.0"
    port: int = 8000

    # DeepSeek API配置
    deepseek_api_key: str
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"

    # 数据库配置
    database_url: str = "sqlite:///./ai_app.db"

    # 日志配置
    log_level: str = "INFO"
    log_format: str = "json"

    # API配置
    api_prefix: str = "/api"
    cors_origins: list[str] = ["*"]

    # 流式响应配置
    stream_timeout: int = 300  # 流式响应超时时间（秒）
    max_concurrent_streams: int = 100  # 最大并发流数量

    # 安全配置（禁用状态）
    enable_auth: bool = False
    enable_rate_limit: bool = False


@lru_cache()
def get_settings() -> Settings:
    """获取缓存的配置实例"""
    return Settings()


# 全局配置实例
settings = get_settings()