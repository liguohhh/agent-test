"""
数据库连接管理

提供数据库连接、引擎管理和会话创建功能
"""

from typing import Annotated, Generator

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.config import settings


class DatabaseManager:
    """数据库管理器

    负责数据库连接的创建、配置和会话管理
    """

    def __init__(self):
        self._engine = None
        self._session_factory = None

    @property
    def engine(self) -> Engine:
        """获取数据库引擎"""
        if self._engine is None:
            self._engine = create_engine(
                settings.database_url,
                echo=settings.debug,
                future=True,
                # SQLite特定配置
                connect_args={"check_same_thread": False} if "sqlite" in settings.database_url else {}
            )

            # 启用SQLite外键约束
            if "sqlite" in settings.database_url:
                self._enable_sqlite_foreign_keys(self._engine)

        return self._engine

    def _enable_sqlite_foreign_keys(self, engine: Engine) -> None:
        """为SQLite启用外键约束"""
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

    @property
    def session_factory(self) -> sessionmaker:
        """获取会话工厂"""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                bind=self.engine,
                autocommit=False,
                autoflush=False,
                future=True
            )
        return self._session_factory

    def create_session(self) -> Session:
        """创建新的数据库会话"""
        return self.session_factory()

    def close(self) -> None:
        """关闭数据库连接"""
        if self._engine:
            self._engine.dispose()
            self._engine = None
            self._session_factory = None


# 全局数据库管理器实例
db_manager = DatabaseManager()


def get_engine() -> Engine:
    """获取数据库引擎"""
    return db_manager.engine


def get_db() -> Generator[Session, None, None]:
    """获取数据库会话依赖注入

    用于FastAPI的依赖注入系统，提供请求级别的数据库会话
    """
    session = db_manager.create_session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


# 类型注解别名，用于依赖注入
DbSession = Annotated[Session, get_db]