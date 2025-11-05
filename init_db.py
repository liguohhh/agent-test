"""
数据库初始化脚本

独立运行，用于初始化数据库表结构
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.database import init_database, reset_database
from app.config import settings


def main():
    """主函数"""
    print(f"正在初始化数据库: {settings.database_url}")
    print(f"应用名称: {settings.app_name}")
    print(f"版本: {settings.app_version}")

    try:
        # 检查是否要重置数据库
        if len(sys.argv) > 1 and sys.argv[1] == "--reset":
            print("警告：正在重置数据库，所有数据将被删除...")
            reset_database()
            print("数据库重置完成")
        else:
            init_database()
            print("数据库初始化完成")

    except Exception as e:
        print(f"数据库初始化失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()