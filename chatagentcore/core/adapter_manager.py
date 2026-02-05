"""Adapter manager for managing platform adapters"""

import asyncio
from typing import Dict, Optional, Type
from loguru import logger
from chatagentcore.adapters.base import BaseAdapter, Message


class AdapterManager:
    """适配器管理器 - 负责适配器的加载、卸载、重载和状态管理"""

    def __init__(self):
        self._adapters: Dict[str, BaseAdapter] = {}
        self._adapter_classes: Dict[str, Type[BaseAdapter]] = {}
        self._running = False

    def register(self, platform: str, adapter_class: Type[BaseAdapter]) -> None:
        """
        注册适配器类

        Args:
            platform: 平台名称 feishu | wecom | dingtalk
            adapter_class: 适配器类，必须继承自 BaseAdapter
        """
        if not issubclass(adapter_class, BaseAdapter):
            raise TypeError(f"{adapter_class} must inherit from BaseAdapter")
        self._adapter_classes[platform] = adapter_class
        logger.info(f"Registered adapter class for platform: {platform}")

    async def load_adapter(
        self, platform: str, config: Dict, adapter_class: Optional[Type[BaseAdapter]] = None
    ) -> BaseAdapter:
        """
        加载并启动适配器

        Args:
            platform: 平台名称
            config: 平台配置
            adapter_class: 适配器类（可选，未注册时必须提供）

        Returns:
            加载的适配器实例

        Raises:
            ValueError: 适配器类未注册或平台已加载
        """
        if platform in self._adapters:
            logger.warning(f"Platform {platform} already loaded, skipping")
            return self._adapters[platform]

        # 获取适配器类
        cls = adapter_class or self._adapter_classes.get(platform)
        if cls is None:
            raise ValueError(f"No adapter class registered for platform: {platform}")

        logger.info(f"Loading adapter for platform: {platform}")

        # 创建适配器实例
        adapter = cls(config)

        # 初始化适配器
        try:
            await adapter.initialize()
            self._adapters[platform] = adapter
            logger.info(f"Adapter loaded successfully for platform: {platform}")
            return adapter
        except Exception as e:
            logger.error(f"Failed to initialize adapter for {platform}: {e}")
            raise

    async def unload_adapter(self, platform: str) -> None:
        """
        卸载适配器

        Args:
            platform: 平台名称
        """
        if platform not in self._adapters:
            logger.warning(f"Platform {platform} not loaded, skipping")
            return

        logger.info(f"Unloading adapter for platform: {platform}")

        adapter = self._adapters[platform]
        try:
            await adapter.shutdown()
            del self._adapters[platform]
            logger.info(f"Adapter unloaded for platform: {platform}")
        except Exception as e:
            logger.error(f"Error during adapter unload for {platform}: {e}")

    async def reload_adapter(self, platform: str, config: Dict) -> BaseAdapter:
        """
        热重载适配器

        Args:
            platform: 平台名称
            config: 新的平台配置

        Returns:
            重新加载的适配器实例
        """
        logger.info(f"Reloading adapter for platform: {platform}")
        await self.unload_adapter(platform)
        return await self.load_adapter(platform, config)

    def get_adapter(self, platform: str) -> Optional[BaseAdapter]:
        """
        获取已加载的适配器

        Args:
            platform: 平台名称

        Returns:
            适配器实例，不存在则返回 None
        """
        return self._adapters.get(platform)

    def get_all_adapters(self) -> Dict[str, BaseAdapter]:
        """
        获取所有已加载的适配器

        Returns:
            平台名到适配器的映射
        """
        return self._adapters.copy()

    def list_platforms(self) -> list[str]:
        """
        列出所有已加载的平台

        Returns:
            平台名称列表
        """
        return list(self._adapters.keys())

    async def load_all(self, configs: Dict[str, Dict]) -> None:
        """
        加载所有平台适配器

        Args:
            configs: 平台配置字典 {平台名: 配置}
        """
        for platform, config in configs.items():
            try:
                await self.load_adapter(platform, config)
            except Exception as e:
                logger.error(f"Failed to load adapter for {platform}: {e}")

    async def unload_all(self) -> None:
        """卸载所有适配器"""
        platforms = list(self._adapters.keys())
        for platform in platforms:
            await self.unload_adapter(platform)

    async def health_check(self, platform: str) -> bool:
        """
        检查平台健康状态

        Args:
            platform: 平台名称

        Returns:
            True 表示健康，False 表示异常
        """
        adapter = self.get_adapter(platform)
        if adapter is None:
            return False
        try:
            return await adapter.health_check()
        except Exception as e:
            logger.error(f"Health check failed for {platform}: {e}")
            return False

    async def broadcast_message(
        self, message: str, platforms: list[str] | None = None
    ) -> Dict[str, str]:
        """
        向多个平台广播消息

        Args:
            message: 要发送的消息内容
            platforms: 目标平台列表，None 表示所有已加载平台

        Returns:
            发送结果 {平台名: 消息ID 或错误信息}
        """
        target_platforms = platforms or self.list_platforms()
        results: Dict[str, str] = {}

        for platform in target_platforms:
            adapter = self.get_adapter(platform)
            if adapter is None:
                results[platform] = "Adapter not loaded"
                continue

            try:
                msg_id = await adapter.send_message(
                    to="broadcast", message_type="text", content=message
                )
                results[platform] = msg_id
            except Exception as e:
                logger.error(f"Failed to broadcast to {platform}: {e}")
                results[platform] = f"Error: {e}"

        return results

    @property
    def loaded_platforms_count(self) -> int:
        """已加载的平台数量"""
        return len(self._adapters)


# 全局适配器管理器实例
_adapter_manager: AdapterManager | None = None


def get_adapter_manager() -> AdapterManager:
    """获取全局适配器管理器实例"""
    global _adapter_manager
    if _adapter_manager is None:
        _adapter_manager = AdapterManager()
    return _adapter_manager


__all__ = ["AdapterManager", "get_adapter_manager"]
