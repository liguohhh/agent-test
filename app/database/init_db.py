"""
数据库初始化模块

负责数据库表的创建和初始化工作
"""

from sqlalchemy import text

from app.database.connection import get_engine
from app.models import Base  # 导入所有模型


def init_database() -> None:
    """初始化数据库

    创建所有定义的表结构
    """
    engine = get_engine()

    # 创建所有表
    Base.metadata.create_all(bind=engine)

    # 创建索引以提升查询性能
    _create_indexes(engine)


def _create_indexes(engine) -> None:
    """创建数据库索引"""

    indexes = [
        # 对话记录表索引
        "CREATE INDEX IF NOT EXISTS idx_conversations_id ON conversations(conversation_id)",
        "CREATE INDEX IF NOT EXISTS idx_conversations_function ON conversations(function_id)",
        "CREATE INDEX IF NOT EXISTS idx_conversations_created_at ON conversations(created_at)",
        "CREATE INDEX IF NOT EXISTS idx_conversations_status ON conversations(status)",
        "CREATE INDEX IF NOT EXISTS idx_conversations_model ON conversations(model_used)",
    ]

    with engine.connect() as conn:
        for index_sql in indexes:
            conn.execute(text(index_sql))
        conn.commit()


def reset_database() -> None:
    """重置数据库

    删除所有表并重新创建
    """
    engine = get_engine()

    # 删除所有表
    Base.metadata.drop_all(bind=engine)

    # 重新创建表
    Base.metadata.create_all(bind=engine)

    # 创建索引
    _create_indexes(engine)