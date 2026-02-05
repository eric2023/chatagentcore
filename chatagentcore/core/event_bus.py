"""Event bus for pub/sub pattern"""

import asyncio
from typing import Callable, Dict, List, Any, Set
from loguru import logger


class EventBus:
    """事件总线 - 发布订阅模式"""

    def __init__(self):
        self._subscribers: Dict[str, Set[asyncio.Queue]] = {}
        self._handlers: Dict[str, List[Callable]] = {}
        self._running = False
        self._dispatch_task: asyncio.Task | None = None

    async def publish(self, channel: str, event: Any) -> None:
        """
        发布事件

        Args:
            channel: 通道名称，支持通配符如 "message:*"
            event: 事件数据
        """
        logger.debug(f"Publishing event to channel: {channel}")

        # 发布到精确匹配的订阅者
        for queue in self._subscribers.get(channel, set()):
            try:
                await queue.put({"channel": channel, "event": event})
            except Exception as e:
                logger.error(f"Error publishing to queue: {e}")

        # 发布到通配符订阅者
        for pattern, queues in self._subscribers.items():
            if "*" in pattern:
                if self._match_pattern(channel, pattern):
                    for queue in queues:
                        try:
                            await queue.put({"channel": channel, "event": event})
                        except Exception as e:
                            logger.error(f"Error publishing to wildcard queue: {e}")

    async def subscribe(self, channel: str) -> asyncio.Queue:
        """
        订阅事件通道

        Args:
            channel: 通道名称，支持通配符如 "message:*"

        Returns:
            用于接收事件的队列
        """
        if channel not in self._subscribers:
            self._subscribers[channel] = set()

        queue: asyncio.Queue = asyncio.Queue(maxsize=1000)
        self._subscribers[channel].add(queue)
        logger.debug(f"Subscribed to channel: {channel}")
        return queue

    async def unsubscribe(self, channel: str, queue: asyncio.Queue) -> None:
        """
        取消订阅

        Args:
            channel: 通道名称
            queue: 之前订阅时返回的队列
        """
        if channel in self._subscribers:
            self._subscribers[channel].discard(queue)
            if not self._subscribers[channel]:
                del self._subscribers[channel]
            logger.debug(f"Unsubscribed from channel: {channel}")

    def on(self, event_type: str, handler: Callable) -> None:
        """
        注册事件处理器（同步回调）

        Args:
            event_type: 事件类型
            handler: 处理函数，签名为 handler(event: Any) -> None
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        self._handlers[event_type].append(handler)
        logger.debug(f"Registered handler for event: {event_type}")

    def off(self, event_type: str, handler: Callable) -> None:
        """
        移除事件处理器

        Args:
            event_type: 事件类型
            handler: 处理函数
        """
        if event_type in self._handlers:
            self._handlers[event_type].remove(handler)
            if not self._handlers[event_type]:
                del self._handlers[event_type]
            logger.debug(f"Removed handler for event: {event_type}")

    async def emit(self, event_type: str, event: Any) -> None:
        """
        触发事件调用处理器

        Args:
            event_type: 事件类型
            event: 事件数据
        """
        for handler in self._handlers.get(event_type, []):
            try:
                if asyncio.iscoroutinefunction(handler):
                    await handler(event)
                else:
                    handler(event)
            except Exception as e:
                logger.error(f"Error in event handler for {event_type}: {e}")

    def _match_pattern(self, value: str, pattern: str) -> bool:
        """
        匹配通配符模式

        Args:
            value: 实际值
            pattern: 模式（仅支持末尾 *）
        """
        if not pattern.endswith("*"):
            return value == pattern
        prefix = pattern[:-1]
        return value.startswith(prefix)

    async def start(self) -> None:
        """启动事件总线"""
        if self._running:
            return
        self._running = True
        logger.info("Event bus started")

    async def stop(self) -> None:
        """停止事件总线"""
        self._running = False
        if self._dispatch_task:
            self._dispatch_task.cancel()
            try:
                await self._dispatch_task
            except asyncio.CancelledError:
                pass

        # 清空所有订阅
        self._subscribers.clear()
        self._handlers.clear()
        logger.info("Event bus stopped")

    @property
    def running(self) -> bool:
        """是否正在运行"""
        return self._running


# 全局事件总线实例
_event_bus: EventBus | None = None


def get_event_bus() -> EventBus:
    """获取全局事件总线实例"""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


__all__ = ["EventBus", "get_event_bus"]
