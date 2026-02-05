"""Feishu platform models"""

from typing import Any, Dict, Optional
from pydantic import BaseModel, Field


class FeishuEventHeader(BaseModel):
    """飞书事件头"""

    event_type: str = Field(..., description="事件类型")
    event_id: str = Field(..., description="事件 ID")
    app_id: str = Field(..., description="应用 ID")
    create_time: str = Field(..., description="创建时间")
    token: str = Field(..., description="验证令牌")


class FeishuEventSender(BaseModel):
    """飞书事件发送者"""

    sender_id: Dict[str, str] = Field(default_factory=dict, description="发送者 ID")
    sender_type: str = Field("user", description="发送者类型: user | app")


class FeishuMessage(BaseModel):
    """飞书消息"""

    message_id: str = Field(..., description="消息 ID")
    chat_type: str = Field(..., description="聊天类型: p2p | group")
    msg_type: str = Field(..., description="消息类型: text | image | etc.")
    content: str = Field(..., description="消息内容（JSON 字符串）")


class FeishuEvent(BaseModel):
    """飞书事件"""

    header: FeishuEventHeader
    event: Dict[str, Any] = Field(default_factory=dict)


class FeishuReceiveMessageEvent(BaseModel):
    """飞书接收消息事件"""

    v1: Optional[Dict[str, Any]] = Field(None, alias="1")
    v10: Optional[Dict[str, Any]] = Field(None, alias="10")

    def get_latest(self) -> Optional[Dict[str, Any]]:
        """获取最新版本的事件数据"""
        return self.v10 or self.v1


class FeishuTextContent(BaseModel):
    """飞书文本消息内容"""

    text: str = Field(..., description="文本内容")


class FeishuImageContent(BaseModel):
    """飞书图片消息内容"""

    image_key: str = Field(..., description="图片 key")


class FeishuCardContent(BaseModel):
    """飞书卡片消息内容"""

    elements: list[Dict[str, Any]] = Field(default_factory=list, description="元素列表")


class FeishuSendMessageRequest(BaseModel):
    """飞书发送消息请求"""

    receive_id: str = Field(..., description="接收者 ID")
    receive_id_type: str = Field("open_id", description="接收者 ID 类型")
    msg_type: str = Field("text", description="消息类型")
    content: str = Field(..., description="消息内容（JSON 字符串）")


class FeishuAccessTokenResponse(BaseModel):
    """飞书访问令牌响应"""

    code: int = Field(0, description="响应码: 0 成功")
    msg: str = Field("success", description="响应消息")
    tenant_access_token: str = Field(..., description="租户访问令牌")
    expire: int = Field(7200, description="过期时间（秒）")


# 消息类型到 Content 类的映射
MESSAGE_CONTENT_MODELS = {
    "text": FeishuTextContent,
    "image": FeishuImageContent,
    "interactive": FeishuCardContent,
}

__all__ = [
    "FeishuEventHeader",
    "FeishuEventSender",
    "FeishuMessage",
    "FeishuEvent",
    "FeishuReceiveMessageEvent",
    "FeishuTextContent",
    "FeishuImageContent",
    "FeishuCardContent",
    "FeishuSendMessageRequest",
    "FeishuAccessTokenResponse",
    "MESSAGE_CONTENT_MODELS",
]
