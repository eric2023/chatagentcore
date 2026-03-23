"""上下文令牌缓存

管理 context_token 的内存缓存和过期处理。
"""

import time
import threading
from typing import Optional, Dict
from loguru import logger


# ---------------------------------------------------------------------------
# 上下文令牌缓存
# ---------------------------------------------------------------------------


class ContextCache:
    """Context Token 内存缓存

    缓存从接收消息中获取的 context_token，用于发送消息时携带。
    自动过期机制，默认 TTL 2 小时。
    """

    def __init__(
        self,
        default_ttl: int = 7200,
        cleanup_interval: int = 300,
    ):
        """初始化上下文缓存

        Args:
            default_ttl: 默认存活时间（秒），默认 2 小时
            cleanup_interval: 清理间隔（秒），默认 5 分钟
        """
        self.default_ttl = default_ttl
        self.cache: Dict[str, dict] = {}
        self._lock = threading.Lock()
        self._cleanup_interval = cleanup_interval
        self._last_cleanup = time.time()

        # 缓存条目结构：
        # {
        #     "to_user_id": {
        #         "token": "context_token",
        #         "expire_at": 1732339200.0 (过期时间戳),
        #         "updated_at": 1732332000.0 (更新时间戳),
        #     }
        # }

    def set(
        self,
        to_user_id: str,
        context_token: str,
        ttl: Optional[int] = None,
    ) -> None:
        """设置上下文令牌

        Args:
            to_user_id: 目标用户 ID
            context_token: 上下文令牌
            ttl: 存活时间（秒），None 表示使用默认值
        """
        if ttl is None:
            ttl = self.default_ttl

        expire_at = time.time() + ttl

        with self._lock:
            self.cache[to_user_id] = {
                "token": context_token,
                "expire_at": expire_at,
                "updated_at": time.time(),
            }

        logger.debug(f"ContextToken 已缓存: user={to_user_id}, ttl={ttl}s")

    def get(self, to_user_id: str) -> Optional[str]:
        """获取上下文令牌

        Args:
            to_user_id: 目标用户 ID

        Returns:
            上下文令牌，不存在或已过期返回 None
        """
        self._maybe_cleanup()

        with self._lock:
            entry = self.cache.get(to_user_id)

            if not entry:
                return None

            # 检查是否过期
            if time.time() > entry["expire_at"]:
                del self.cache[to_user_id]
                logger.debug(f"ContextToken 已过期: user={to_user_id}")
                return None

            return entry["token"]

    def remove(self, to_user_id: str) -> bool:
        """删除上下文令牌

        Args:
            to_user_id: 目标用户 ID

        Returns:
            是否成功删除
        """
        with self._lock:
            if to_user_id in self.cache:
                del self.cache[to_user_id]
                logger.debug(f"ContextToken 已移除: user={to_user_id}")
                return True
            return False

    def clear(self) -> None:
        """清空所有缓存"""
        with self._lock:
            count = len(self.cache)
            self.cache.clear()
            logger.debug(f"ContextToken 缓存已清空: {count} 条")

    def _maybe_cleanup(self) -> None:
        """可能清理过期条目"""
        current_time = time.time()

        # 检查是否需要清理
        if current_time - self._last_cleanup < self._cleanup_interval:
            return

        # 执行清理
        self._cleanup()
        self._last_cleanup = current_time

    def _cleanup(self) -> int:
        """清理过期条目

        Returns:
            清理的条目数
        """
        with self._lock:
            current_time = time.time()
            expired_keys = [
                key
                for key, entry in self.cache.items()
                if current_time > entry["expire_at"]
            ]

            for key in expired_keys:
                del self.cache[key]

            if expired_keys:
                logger.debug(f"ContextToken 清理完成: 清理 {len(expired_keys)} 条过期缓存")

            return len(expired_keys)

    def size(self) -> int:
        """获取缓存大小

        Returns:
            缓存条目数
        """
        with self._lock:
            return len(self.cache)

    def info(self) -> Dict[str, any]:
        """获取缓存信息

        Returns:
            缓存信息字典
        """
        with self._lock:
            return {
                "size": len(self.cache),
                "default_ttl": self.default_ttl,
                "cleanup_interval": self._cleanup_interval,
                "last_cleanup": self._last_cleanup,
                "entries": {k: {"expire_at": v["expire_at"]} for k, v in self.cache.items()},
            }
