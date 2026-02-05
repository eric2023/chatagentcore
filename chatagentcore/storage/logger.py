"""Log module using loguru"""

import sys
from pathlib import Path
from loguru import logger as _logger


class LogConfig:
    """日志配置"""

    def __init__(self, log_dir: str | None = None, level: str = "INFO"):
        """
        初始化日志配置

        Args:
            log_dir: 日志文件目录，None 表示不写文件
            level: 日志级别
        """
        self.log_dir = Path(log_dir) if log_dir else None
        self.level = level

    def setup(self) -> None:
        """配置日志输出"""
        # 移除默认处理器
        _logger.remove()

        # 控制台输出
        _logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=self.level,
            colorize=True,
        )

        # 文件输出（如果指定了日志目录）
        if self.log_dir:
            self.log_dir.mkdir(parents=True, exist_ok=True)

            # 普通日志文件
            _logger.add(
                self.log_dir / "chatagentcore.log",
                rotation="10 MB",
                retention="30 days",
                level=self.level,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            )

            # 错误日志文件
            _logger.add(
                self.log_dir / "error.log",
                rotation="10 MB",
                retention="30 days",
                level="ERROR",
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            )


# 创建默认日志实例
logger = _logger

__all__ = ["logger", "LogConfig"]
