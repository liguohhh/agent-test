"""
流式响应管理模块

实现Server-Sent Events (SSE)格式的实时数据传输
"""

import json
import time
import uuid
from typing import Any, Dict, Generator, Optional

from fastapi import HTTPException
from fastapi.responses import StreamingResponse

from app.config import settings
from app.core.exceptions import StreamError


class StreamingResponseManager:
    """流式响应管理器

    负责生成和管理Server-Sent Events格式的流式响应
    """

    def __init__(self):
        self._active_streams: Dict[str, Dict[str, Any]] = {}
        self.max_concurrent_streams = settings.max_concurrent_streams
        self.stream_timeout = settings.stream_timeout

    def create_stream_id(self) -> str:
        """创建唯一的流ID"""
        return str(uuid.uuid4())

    def register_stream(
        self,
        stream_id: str,
        function_id: str,
        client_info: Optional[Dict[str, Any]] = None
    ) -> None:
        """注册新的流"""
        if len(self._active_streams) >= self.max_concurrent_streams:
            raise HTTPException(
                status_code=503,
                detail="服务器繁忙，并发流数量已达上限"
            )

        self._active_streams[stream_id] = {
            "function_id": function_id,
            "created_at": time.time(),
            "last_activity": time.time(),
            "client_info": client_info or {}
        }

    def unregister_stream(self, stream_id: str) -> None:
        """注销流"""
        if stream_id in self._active_streams:
            del self._active_streams[stream_id]

    def update_stream_activity(self, stream_id: str) -> None:
        """更新流的最后活动时间"""
        if stream_id in self._active_streams:
            self._active_streams[stream_id]["last_activity"] = time.time()

    def cleanup_expired_streams(self) -> None:
        """清理过期的流"""
        current_time = time.time()
        expired_streams = []

        for stream_id, stream_info in self._active_streams.items():
            if current_time - stream_info["last_activity"] > self.stream_timeout:
                expired_streams.append(stream_id)

        for stream_id in expired_streams:
            self.unregister_stream(stream_id)

    def get_stream_info(self, stream_id: str) -> Optional[Dict[str, Any]]:
        """获取流信息"""
        return self._active_streams.get(stream_id)

    def get_active_streams_count(self) -> int:
        """获取活跃流数量"""
        return len(self._active_streams)

    def create_sse_response(
        self,
        stream_id: str,
        data_generator: Generator[Dict[str, Any], None, None]
    ) -> StreamingResponse:
        """创建SSE流式响应"""
        def sse_generator():
            try:
                # 更新流活动时间
                self.update_stream_activity(stream_id)

                # 发送连接建立消息
                yield self._format_sse_data({
                    "type": "connected",
                    "stream_id": stream_id,
                    "timestamp": int(time.time())
                })

                # 处理数据流
                for data_chunk in data_generator:
                    # 更新活动时间
                    self.update_stream_activity(stream_id)

                    # 发送数据块
                    yield self._format_sse_data(data_chunk)

                # 发送完成消息
                yield self._format_sse_data({
                    "type": "stream_completed",
                    "stream_id": stream_id,
                    "timestamp": int(time.time())
                })

            except Exception as e:
                # 发送错误消息
                yield self._format_sse_data({
                    "type": "stream_error",
                    "stream_id": stream_id,
                    "error": str(e),
                    "timestamp": int(time.time())
                })
            finally:
                # 清理流
                self.unregister_stream(stream_id)

        return StreamingResponse(
            sse_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Headers": "Cache-Control"
            }
        )

    def _format_sse_data(self, data: Dict[str, Any]) -> str:
        """格式化SSE数据"""
        return f"data: {json.dumps(data, ensure_ascii=False)}\n\n"

    @staticmethod
    def create_error_stream(error_message: str, stream_id: Optional[str] = None) -> Generator[str, None, None]:
        """创建错误流"""
        error_data = {
            "type": "error",
            "message": error_message,
            "timestamp": int(time.time())
        }
        if stream_id:
            error_data["stream_id"] = stream_id

        manager = StreamingResponseManager()
        yield manager._format_sse_data(error_data)

    @staticmethod
    def create_heartbeat_stream(interval: int = 30) -> Generator[str, None, None]:
        """创建心跳流，用于保持连接活跃"""
        manager = StreamingResponseManager()
        while True:
            yield manager._format_sse_data({
                "type": "heartbeat",
                "timestamp": int(time.time())
            })
            time.sleep(interval)


# 全局流式响应管理器实例
streaming_manager = StreamingResponseManager()