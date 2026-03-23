"""日志工具

提供带账号前缀的日志功能，支持敏感信息脱敏。
"""

from typing import Optional
from loguru import logger


def get_adapter_logger(account_id: Optional[str] = None):
    """获取适配器专用日志实例

    Args:
        account_id: 账号 ID，将作为日志前缀

    Returns:
        Logger 实例
    """
    if account_id:
        # 创建带账号前缀的 logger
        logger = logger.bind(account=account_id)
    else:
        logger = logger
    return logger


def redact_token(token: Optional[str]) -> str:
    """脱敏 Token（只显示前 8 位和后 4 位）

    Args:
        token: 原始 Token

    Returns:
        脱敏后的字符串
    """
    if not token:
        return "(none)"
    if len(token) <= 12:
        return token[:4] + "..."
    return token[:8] + "..." + token[-4:]


def redact_user_id(user_id: Optional[str]) -> str:
    """脱敏用户 ID

    Args:
        user_id: 原始用户 ID

    Returns:
        脱敏后的字符串
    """
    if not user_id:
        return "(none)"
    if user_id.endswith("@im.wechat"):
        # 只保留前 8 位
        return user_id[:8] + "..." + user_id[-9:]
    if len(user_id) > 12:
        return user_id[:8] + "...***"
    return user_id[:4] + "***"


def redact_body(body: str, max_length: int = 200) -> str:
    """脱敏请求/响应体

    Args:
        body: 原始内容
        max_length: 截断长度

    Returns:
        脱敏后的字符串
    """
    if len(body) > max_length:
        return body[:max_length] + f"... ({len(body)} chars)"
    return body
