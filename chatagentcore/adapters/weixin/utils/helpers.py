"""辅助工具函数

提供 ID 规范化、Header 构建、随机 UIN 生成等辅助功能。
"""

import base64
import json
import hashlib
import secrets
from typing import Optional, Dict, Any

# ---------------------------------------------------------------------------
# ID 规范化
# ---------------------------------------------------------------------------

def normalize_account_id(account_id: str) -> str:
    """规范化账号 ID，替换特殊字符为连字符

    Args:
        account_id: 原始账号 ID

    Returns:
        规范化后的账号 ID
    """
    # 替换常见特殊字符
    normalized = account_id.replace("@", "-").replace(".", "-").replace("_", "-")
    return normalized


# ---------------------------------------------------------------------------
# Header 构建
# ---------------------------------------------------------------------------

DEFAULT_CHANNEL_VERSION = "1.0.0"


def build_request_headers(token: Optional[str] = None, route_tag: Optional[str] = None) -> Dict[str, str]:
    """构建微信 API 请求标准 Headers

    Args:
        token: Bot Token（可选）
        route_tag: 路由标签（可选，用于流量控制）

    Returns:
        请求 Headers
    """
    headers = {
        "Content-Type": "application/json",
        "AuthorizationType": "ilink_bot_token",
        "X-WECHAT-UIN": generate_random_uin(),
    }

    if token and token.strip():
        headers["Authorization"] = f"Bearer {token.strip()}"

    if route_tag:
        headers["SKRouteTag"] = str(route_tag)

    return headers


def build_base_info() -> Dict[str, str]:
    """构建请求元数据

    Returns:
        base_info 字典
    """
    return {
        "channel_version": DEFAULT_CHANNEL_VERSION,
    }


# ---------------------------------------------------------------------------
# 随机 UIN 生成
# ---------------------------------------------------------------------------

def generate_random_uin() -> str:
    """生成随机 UIN（X-WECHAT-UIN Header）

    格式：随机 uint32 → 十进制字符串 → base64

    Returns:
        base64 编码的 UIN
    """
    uint32 = secrets.randbelow(2**32)
    uin_string = str(uint32)
    return base64.b64encode(uin_string.encode('utf-8')).decode('utf-8')


# ---------------------------------------------------------------------------
# URL 处理
# ---------------------------------------------------------------------------

def ensure_trailing_slash(url: str) -> str:
    """确保 URL 以 / 结尾

    Args:
        url: 原始 URL

    Returns:
        以 / 结尾的 URL
    """
    return url.rstrip('/') + '/'


# ---------------------------------------------------------------------------
# JSON 处理
# ---------------------------------------------------------------------------

def json_dumps(obj: Any, ensure_ascii: bool = False) -> str:
    """安全的 JSON 序列化

    Args:
        obj: 要序列化的对象
        ensure_ascii: 是否确保 ASCII

    Returns:
        JSON 字符串
    """
    return json.dumps(obj, ensure_ascii=ensure_ascii, separators=(',', ':'))


def json_loads(text: str) -> Any:
    """安全的 JSON 反序列化

    Args:
        text: JSON 字符串

    Returns:
        反序列化后的对象

    Raises:
        ValueError: JSON 解析失败
    """
    try:
        return json.loads(text)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON 解析失败: {e}") from e


# ---------------------------------------------------------------------------
# 时间处理
# ---------------------------------------------------------------------------

import time


def get_current_timestamp_ms() -> int:
    """获取当前时间戳（毫秒）

    Returns:
        当前时间戳（毫秒）
    """
    return int(time.time() * 1000)


def get_current_timestamp_s() -> int:
    """获取当前时间戳（秒）

    Returns:
        当前时间戳（秒）
    """
    return int(time.time())
