"""
简单缓存模块

提供内存缓存功能，支持TTL过期
"""

import hashlib
import time
import json
from typing import Any, Dict, Optional

from app.config import settings
from app.core.exceptions import CacheError


class SimpleCache:
    """简单内存缓存实现"""

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self.default_ttl = settings.cache_ttl
        self.max_size = 1000  # 最大缓存条目数

    def _generate_key(self, function_id: str, input_data: Dict[str, Any]) -> str:
        """生成缓存键"""
        # 创建基于function_id和输入数据的哈希键
        key_data = {
            "function_id": function_id,
            "input": input_data
        }
        key_str = json.dumps(key_data, sort_keys=True, ensure_ascii=False)
        return hashlib.md5(key_str.encode('utf-8')).hexdigest()

    def get(self, function_id: str, input_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """获取缓存数据"""
        if not settings.enable_cache:
            return None

        key = self._generate_key(function_id, input_data)

        if key not in self._cache:
            return None

        cache_entry = self._cache[key]

        # 检查是否过期
        if time.time() > cache_entry["expires_at"]:
            del self._cache[key]
            return None

        # 更新访问时间
        cache_entry["accessed_at"] = time.time()
        return cache_entry["data"]

    def set(
        self,
        function_id: str,
        input_data: Dict[str, Any],
        result: Dict[str, Any],
        ttl: Optional[int] = None
    ) -> None:
        """设置缓存数据"""
        if not settings.enable_cache:
            return

        try:
            key = self._generate_key(function_id, input_data)

            # 如果缓存已满，删除最久未访问的条目
            if len(self._cache) >= self.max_size:
                self._evict_lru()

            ttl = ttl or self.default_ttl
            current_time = time.time()

            self._cache[key] = {
                "data": result,
                "created_at": current_time,
                "accessed_at": current_time,
                "expires_at": current_time + ttl,
                "function_id": function_id
            }

        except Exception as e:
            # 缓存错误不应该影响主流程
            print(f"缓存设置失败: {e}")

    def delete(self, function_id: str, input_data: Dict[str, Any]) -> bool:
        """删除缓存数据"""
        key = self._generate_key(function_id, input_data)
        if key in self._cache:
            del self._cache[key]
            return True
        return False

    def clear(self) -> None:
        """清空所有缓存"""
        self._cache.clear()

    def clear_by_function(self, function_id: str) -> int:
        """清除指定功能的所有缓存"""
        keys_to_delete = [
            key for key, entry in self._cache.items()
            if entry.get("function_id") == function_id
        ]

        for key in keys_to_delete:
            del self._cache[key]

        return len(keys_to_delete)

    def _evict_lru(self) -> None:
        """删除最久未访问的缓存条目"""
        if not self._cache:
            return

        # 找到最久未访问的条目
        lru_key = min(
            self._cache.keys(),
            key=lambda k: self._cache[k]["accessed_at"]
        )
        del self._cache[lru_key]

    def cleanup_expired(self) -> int:
        """清理过期的缓存条目"""
        current_time = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if current_time > entry["expires_at"]
        ]

        for key in expired_keys:
            del self._cache[key]

        return len(expired_keys)

    def get_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        current_time = time.time()
        expired_count = sum(
            1 for entry in self._cache.values()
            if current_time > entry["expires_at"]
        )

        # 按功能统计
        function_stats = {}
        for entry in self._cache.values():
            func_id = entry.get("function_id", "unknown")
            function_stats[func_id] = function_stats.get(func_id, 0) + 1

        return {
            "total_entries": len(self._cache),
            "expired_entries": expired_count,
            "active_entries": len(self._cache) - expired_count,
            "max_size": self.max_size,
            "usage_ratio": len(self._cache) / self.max_size,
            "function_distribution": function_stats
        }


# 全局缓存实例
cache = SimpleCache()