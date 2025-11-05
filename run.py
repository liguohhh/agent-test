"""
应用启动脚本

用于启动AI应用后端服务
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import uvicorn
from app.config import settings


def main():
    """主函数"""
    print(f"正在启动 {settings.app_name} v{settings.app_version}")
    print(f"环境: {'开发环境' if settings.debug else '生产环境'}")
    print(f"服务地址: http://{settings.host}:{settings.port}")
    print(f"API文档: http://{settings.host}:{settings.port}/docs")
    print(f"数据库: {settings.database_url}")
    print(f"DeepSeek模型: {settings.deepseek_model}")
    print(f"缓存: {'启用' if settings.enable_cache else '禁用'}")
    print("-" * 50)

    try:
        uvicorn.run(
            "app.main:app",
            host=settings.host,
            port=settings.port,
            reload=settings.debug,
            log_level=settings.log_level.lower(),
            access_log=True
        )
    except KeyboardInterrupt:
        print("\n应用已停止")
    except Exception as e:
        print(f"启动失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()