"""微信适配器 - 支持 iLink AI 微信聊天 API

基于 openclaw-weixin 插件的协议实现，提供完整的微信聊天功能支持。

主要功能：
- 扫码登录
- 长轮询接收消息
- 发送文本/图片/视频/文件/语音消息
- 媒体文件上传下载（AES-128-ECB 加密）
- 输入状态指示
- 会话管理

协议参考：腾讯 openclaw-weixin 插件 (https://github.com/anthropics/openclaw)
"""

from .main import WeixinAdapter
from .models.message import (
    BaseInfo,
    MessageType,
    MessageItemType,
    MessageState,
    TextItem,
    CDNMedia,
    ImageItem,
    VoiceItem,
    FileItem,
    VideoItem,
    MessageItem,
    WeixinMessage,
    RefMessage,
)
from .models.media import (
    MediaType,
    GetUploadUrlReq,
    GetUploadUrlResp,
)
from .models.auth import (
    QrcodeResponse,
    QrcodeStatus,
    LoginResult,
    DEFAULT_ILINK_BOT_TYPE,
)
from .api.auth import AuthAPI
from .api.messaging import MessagingAPI
from .api.media import MediaAPI
from .crypto.aes_ecb import (
    encrypt_aes_ecb,
    decrypt_aes_ecb,
    aes_ecb_padded_size,
    parse_aes_key,
)

__all__ = [
    # Main adapter
    "WeixinAdapter",
    # Models
    "BaseInfo",
    "MessageType",
    "MessageItemType",
    "MessageState",
    "TextItem",
    "CDNMedia",
    "ImageItem",
    "VoiceItem",
    "FileItem",
    "VideoItem",
    "MessageItem",
    "WeixinMessage",
    "RefMessage",
    "MediaType",
    "GetUploadUrlReq",
    "GetUploadUrlResp",
    "QrcodeResponse",
    "QrcodeStatus",
    "LoginResult",
    "DEFAULT_ILINK_BOT_TYPE",
    # APIs
    "AuthAPI",
    "MessagingAPI",
    "MediaAPI",
    # Crypto
    "encrypt_aes_ecb",
    "decrypt_aes_ecb",
    "aes_ecb_padded_size",
    "parse_aes_key",
]

# 版本信息
VERSION = "1.0.0"
