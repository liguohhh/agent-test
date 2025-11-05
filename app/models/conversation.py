"""
对话记录数据模型

定义对话记录表的ORM模型，存储用户输入和AI回复结果
"""

from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime, Integer, String, Text, Numeric
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()


class Conversation(Base):
    """对话记录模型

    存储完整的AI对话记录，包括用户输入和AI回复结果
    """

    __tablename__ = "conversations"

    # 主键字段
    id = Column(Integer, primary_key=True, autoincrement=True, comment="自增主键")

    # 业务标识字段
    conversation_id = Column(String(36), nullable=False, unique=True, comment="UUID格式的对话唯一标识符")
    function_id = Column(String(50), nullable=False, comment="执行的AI功能ID")
    function_name = Column(String(100), nullable=False, comment="功能名称")
    model_used = Column(String(50), nullable=False, comment="实际使用的DeepSeek模型名称")

    # 对话内容字段
    user_input = Column(Text, nullable=False, comment="用户的原始输入文本")
    ai_response = Column(Text, nullable=False, comment="AI生成的完整回复结果")

    # 统计信息字段
    total_tokens = Column(Integer, default=0, comment="整个对话消耗的总Token数量")
    execution_time = Column(Numeric(10, 3), default=0.000, comment="对话执行时间（秒）")

    # 状态字段
    status = Column(String(20), nullable=False, default="completed", comment="对话状态（completed/failed/timeout）")

    # 时间戳字段
    created_at = Column(DateTime, default=func.now(), comment="对话完成时间戳")

    # 扩展字段
    extra_data = Column(Text, comment="JSON格式的额外元数据（如参数配置、错误信息等）")

    def __repr__(self) -> str:
        """模型的字符串表示"""
        return (
            f"<Conversation(id={self.id}, "
            f"conversation_id='{self.conversation_id}', "
            f"function_id='{self.function_id}', "
            f"status='{self.status}')>"
        )

    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            "id": self.id,
            "conversation_id": self.conversation_id,
            "function_id": self.function_id,
            "function_name": self.function_name,
            "model_used": self.model_used,
            "user_input": self.user_input,
            "ai_response": self.ai_response,
            "total_tokens": self.total_tokens,
            "execution_time": float(self.execution_time),
            "status": self.status,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "metadata": self.extra_data
        }