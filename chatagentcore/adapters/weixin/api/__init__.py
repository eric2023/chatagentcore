"""微信适配器 API 层"""

from .client import WeixinHTTPClient
from .auth import AuthAPI
from .messaging import MessagingAPI
from .media import MediaAPI

__all__ = [
    "WeixinHTTPClient",
    "AuthAPI",
    "MessagingAPI",
    "MediaAPI",
]
