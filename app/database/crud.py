"""
数据库CRUD操作

提供对话记录的创建、查询、更新和删除操作
"""

import json
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session
from sqlalchemy.sql import text

from app.models.conversation import Conversation


class ConversationCRUD:
    """对话记录CRUD操作类"""

    def __init__(self, db: Session):
        self.db = db

    def create_conversation(
        self,
        function_id: str,
        function_name: str,
        model_used: str,
        user_input: str,
        ai_response: str,
        total_tokens: int = 0,
        execution_time: float = 0.0,
        status: str = "completed",
        metadata: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """创建新的对话记录"""
        conversation = Conversation(
            conversation_id=str(uuid.uuid4()),
            function_id=function_id,
            function_name=function_name,
            model_used=model_used,
            user_input=user_input,
            ai_response=ai_response,
            total_tokens=total_tokens,
            execution_time=execution_time,
            status=status,
            extra_data=json.dumps(metadata) if metadata else None
        )

        self.db.add(conversation)
        self.db.commit()
        self.db.refresh(conversation)
        return conversation

    def get_conversation_by_id(self, conversation_id: str) -> Optional[Conversation]:
        """根据ID获取对话记录"""
        return self.db.query(Conversation).filter(
            Conversation.conversation_id == conversation_id
        ).first()

    def get_conversations_by_function_id(
        self,
        function_id: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Conversation]:
        """根据功能ID获取对话记录列表"""
        return self.db.query(Conversation).filter(
            Conversation.function_id == function_id
        ).order_by(Conversation.created_at.desc()).offset(offset).limit(limit).all()

    def get_conversations_by_status(
        self,
        status: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Conversation]:
        """根据状态获取对话记录列表"""
        return self.db.query(Conversation).filter(
            Conversation.status == status
        ).order_by(Conversation.created_at.desc()).offset(offset).limit(limit).all()

    def get_all_conversations(
        self,
        limit: int = 100,
        offset: int = 0
    ) -> List[Conversation]:
        """获取所有对话记录"""
        return self.db.query(Conversation).order_by(
            Conversation.created_at.desc()
        ).offset(offset).limit(limit).all()

    def update_conversation_status(
        self,
        conversation_id: str,
        status: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Conversation]:
        """更新对话记录状态"""
        conversation = self.get_conversation_by_id(conversation_id)
        if conversation:
            conversation.status = status
            if metadata:
                conversation.extra_data = json.dumps(metadata)
            self.db.commit()
            self.db.refresh(conversation)
        return conversation

    def delete_conversation(self, conversation_id: str) -> bool:
        """删除对话记录"""
        conversation = self.get_conversation_by_id(conversation_id)
        if conversation:
            self.db.delete(conversation)
            self.db.commit()
            return True
        return False

    def get_conversation_statistics(self) -> Dict[str, Any]:
        """获取对话统计信息"""
        stats = self.db.execute(text("""
            SELECT
                COUNT(*) as total_conversations,
                COUNT(CASE WHEN status = 'completed' THEN 1 END) as completed_count,
                COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_count,
                COUNT(CASE WHEN status = 'timeout' THEN 1 END) as timeout_count,
                AVG(total_tokens) as avg_tokens,
                AVG(execution_time) as avg_execution_time,
                MAX(created_at) as last_conversation_time
            FROM conversations
        """)).fetchone()

        # 按功能ID统计
        function_stats = self.db.execute(text("""
            SELECT
                function_id,
                function_name,
                COUNT(*) as count,
                AVG(total_tokens) as avg_tokens,
                AVG(execution_time) as avg_execution_time
            FROM conversations
            WHERE status = 'completed'
            GROUP BY function_id, function_name
            ORDER BY count DESC
        """)).fetchall()

        return {
            "total_conversations": stats.total_conversations or 0,
            "completed_count": stats.completed_count or 0,
            "failed_count": stats.failed_count or 0,
            "timeout_count": stats.timeout_count or 0,
            "avg_tokens": float(stats.avg_tokens or 0),
            "avg_execution_time": float(stats.avg_execution_time or 0),
            "last_conversation_time": stats.last_conversation_time.isoformat() if stats.last_conversation_time else None,
            "function_statistics": [
                {
                    "function_id": row.function_id,
                    "function_name": row.function_name,
                    "count": row.count,
                    "avg_tokens": float(row.avg_tokens or 0),
                    "avg_execution_time": float(row.avg_execution_time or 0)
                }
                for row in function_stats
            ]
        }

    def search_conversations(
        self,
        query: str,
        limit: int = 100,
        offset: int = 0
    ) -> List[Conversation]:
        """搜索对话记录（搜索用户输入和AI回复）"""
        search_pattern = f"%{query}%"
        return self.db.query(Conversation).filter(
            (Conversation.user_input.like(search_pattern)) |
            (Conversation.ai_response.like(search_pattern))
        ).order_by(Conversation.created_at.desc()).offset(offset).limit(limit).all()

    def get_conversations_by_date_range(
        self,
        start_date: datetime,
        end_date: datetime,
        limit: int = 100,
        offset: int = 0
    ) -> List[Conversation]:
        """根据日期范围获取对话记录"""
        return self.db.query(Conversation).filter(
            Conversation.created_at >= start_date,
            Conversation.created_at <= end_date
        ).order_by(Conversation.created_at.desc()).offset(offset).limit(limit).all()