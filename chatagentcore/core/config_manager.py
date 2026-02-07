"""Configuration manager with YAML support and hot reload"""

import asyncio
import json
import os
from pathlib import Path
from typing import Dict, Any, Optional, Callable
import yaml
from loguru import logger
from chatagentcore.api.schemas.config import Settings, PlatformsConfig


class ConfigManager:
    """配置管理器 - 支持加载、热重载和验证"""

    def __init__(self, config_path: str = "config/config.yaml"):
        """
        初始化配置管理器

        Args:
            config_path: 配置文件路径
        """
        self.config_path = Path(config_path)
        # uos-ai 预设的配置文件路径
        self.uos_ai_config_path = Path(os.path.expanduser("~/.config/deepin/uos-ai-assistant/chatagentcore.yaml"))
        self.version: int = 0
        self._config: Settings | None = None
        self._raw_config: Dict[str, Any] = {}
        self._reload_task: asyncio.Task | None = None
        self._reload_interval: float = 5.0  # 秒
        self._callbacks: list[Callable[[Settings], None]] = []

    def load(self) -> Settings:
        """
        加载配置文件
        """
        # 1. 确保服务自身配置目录存在
        if not self.config_path.parent.exists():
            self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # 2. 加载或创建服务配置
        if not self.config_path.exists():
            logger.warning(f"Config file not found: {self.config_path}, creating default config")
            self._config = Settings()
            # 设置初始默认 Token
            self._config.auth.token = "uos-ai-assistant-internal-token"
            self._save_to_file(self._config.model_dump())
            self._raw_config = self._config.model_dump()
        else:
            logger.info(f"Loading config from: {self.config_path}")
            with open(self.config_path, "r", encoding="utf-8") as f:
                self._raw_config = yaml.safe_load(f) or {}
            self._config = Settings.model_validate(self._raw_config)

        # 3. 强制在 uos-ai 指定路径同步配置文件
        self._sync_to_uos_ai_path()

        self._validate_config(self._config)
        
        # 确保日志目录存在
        log_file = Path(self._config.logging.file)
        if not log_file.parent.exists():
            log_file.parent.mkdir(parents=True, exist_ok=True)

        self.version += 1
        return self._config

    def _sync_to_uos_ai_path(self):
        """同步配置到 uos-ai 指定的 ~/.config/... 路径"""
        try:
            if not self.uos_ai_config_path.parent.exists():
                self.uos_ai_config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 构造 uos-ai 需要的具体内容
            uos_config = {
                "server": {
                    "host": "localhost",
                    "port": self._config.server.port,
                    "debug": self._config.server.debug
                },
                "auth": {
                    "type": "fixed_token",
                    "token": self._config.auth.token
                }
            }
            
            with open(self.uos_ai_config_path, "w", encoding="utf-8") as f:
                yaml.dump(uos_config, f, allow_unicode=True, sort_keys=False)
            
            logger.info(f"已同步配置文件至 uos-ai 路径: {self.uos_ai_config_path}")
        except Exception as e:
            logger.error(f"同步 uos-ai 配置文件失败: {e}")

    def _save_to_file(self, config_dict: Dict[str, Any]) -> None:
        """内部方法：将字典保存到 YAML 文件"""
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                yaml.dump(config_dict, f, allow_unicode=True, sort_keys=False)
        except Exception as e:
            logger.error(f"Failed to save config: {e}")

    def reload(self) -> Settings:
        """重新加载配置"""
        logger.info("Reloading config...")
        old_raw = json.dumps(self._raw_config, sort_keys=True)
        try:
            self.load()
            new_raw = json.dumps(self._raw_config, sort_keys=True)
            if old_raw != new_raw:
                logger.info("Config content changed, triggering callbacks")
                for callback in self._callbacks:
                    try: callback(self._config)
                    except Exception as e: logger.error(f"Error in config callback: {e}")
        except Exception as e:
            logger.error(f"Reload failed: {e}")
        return self._config

    async def watch(self, interval: float = 5.0) -> None:
        self._reload_interval = interval
        self._reload_task = asyncio.create_task(self._watch_loop())
        logger.info(f"Config watch task started (interval: {interval}s)")

    async def stop_watch(self) -> None:
        if self._reload_task:
            self._reload_task.cancel()
            try: await self._reload_task
            except asyncio.CancelledError: pass

    def on_change(self, callback: Callable[[Settings], None]) -> None:
        self._callbacks.append(callback)

    @property
    def config(self) -> Settings:
        if self._config is None: raise RuntimeError("Config not loaded.")
        return self._config

    @property
    def platforms(self) -> PlatformsConfig:
        return self.config.platforms

    def _validate_config(self, config: Settings) -> None:
        enabled_platforms = [n for n, p in [("feishu", config.platforms.feishu), ("wecom", config.platforms.wecom), 
                            ("dingtalk", config.platforms.dingtalk), ("qq", config.platforms.qq)] if p.enabled]
        logger.info(f"Enabled platforms: {enabled_platforms or 'None'}")

    async def _watch_loop(self) -> None:
        if not self.config_path.exists(): return
        last_mtime = self.config_path.stat().st_mtime
        try:
            while True:
                await asyncio.sleep(self._reload_interval)
                if not self.config_path.exists(): break
                current_mtime = self.config_path.stat().st_mtime
                if current_mtime != last_mtime:
                    self.reload()
                    last_mtime = current_mtime
        except asyncio.CancelledError: pass

    def to_dict(self) -> Dict[str, Any]:
        return self._config.model_dump() if self._config else {}


_config_manager: ConfigManager | None = None

def get_config_manager(config_path: str = "config/config.yaml") -> ConfigManager:
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager(config_path)
    return _config_manager

def get_config() -> Settings:
    return get_config_manager().config

__all__ = ["ConfigManager", "get_config_manager", "get_config"]