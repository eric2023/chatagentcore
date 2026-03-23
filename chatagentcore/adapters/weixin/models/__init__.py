"""微信适配器数据模型层"""

from .message import (
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
from .media import (
    MediaType,
    GetUploadUrlReq,
    GetUploadUrlResp,
)
from .auth import (
    QrcodeResponse,
    QrcodeStatus,
    LoginResult,
)

__all__ = [
    # Message models
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
    # Media models
    "MediaType",
    "GetUploadUrlReq",
    "GetUploadUrlResp",
    # Auth models
    "QrcodeResponse",
    "QrcodeStatus",
    "LoginResult",
]
