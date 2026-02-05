"""Base adapter class for chat platforms"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict
from pydantic import BaseModel


class Message(BaseModel):
    """统一消息格式"""

    platform: str  # feishu | wecom | dingtalk
    message_id: str
    sender: Dict[str, Any]  # {"id": "...", "name": "..."}
    conversation: Dict[str, Any]  # {"id": "...", "type": "user|group"}
    content: Dict[str, Any]  # {"type": "text|image|card", "text": "..."}
    timestamp: int


class BaseAdapter(ABC):
    """平台适配器抽象基类

    所有平台适配器必须继承此类并实现抽象方法。
    """

    def __init__(self, config: Dict[str, Any]):
        """
        初始化适配器

        Args:
            config: 平台配置
        """
        self.config = config
        self.platform_name = self.__class__.__name__.lower().replace("adapter", "")

    @abstractmethod
    async def send_message(
        self, to: str, message_type: str, content: str, conversation_type: str = "user"
    ) -> str:
        """
        发送消息到指定接收者

        Args:
            to: 接收者 ID（用户 ID 或群 ID）
            message_type: 消息类型 text | image | card
            content: 消息内容
            conversation_type: 会话类型 user | group

        Returns:
            发送后的消息 ID

        Raises:
            Exception: 发送失败时抛出异常
        """
        pass

    def set_message_handler(self, handler: Callable[[Message], None]):
        """
        设置消息处理器

        Args:
            handler: 消息处理函数，接收 Message 对象
        """
        pass

    async def initialize(self) -> None:
        """初始化适配器（可选实现）"""
        pass

    async def shutdown(self) -> None:
        """关闭适配器（可选实现）"""
        pass

    async def health_check(self) -> bool:
        """
        健康检查

        Returns:
            True 表示适配器正常，False 表示异常
        """
        return True


__all__ = ["BaseAdapter", "Message"]
