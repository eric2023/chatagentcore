"""微信适配器工具函数层"""

from .qr import generate_qrcode, display_qrcode_terminal, display_qrcode_with_qr_code_terminal
from .logger import get_adapter_logger, redact_token, redact_user_id, redact_body
from .helpers import (
    normalize_account_id,
    build_request_headers,
    build_base_info,
    generate_random_uin,
    ensure_trailing_slash,
    json_dumps,
    json_loads,
    get_current_timestamp_ms,
    get_current_timestamp_s,
)

__all__ = [
    "generate_qrcode",
    "display_qrcode_terminal",
    "display_qrcode_with_qr_code_terminal",
    "get_adapter_logger",
    "redact_token",
    "redact_user_id",
    "redact_body",
    "normalize_account_id",
    "build_request_headers",
    "build_base_info",
    "generate_random_uin",
    "ensure_trailing_slash",
    "json_dumps",
    "json_loads",
    "get_current_timestamp_ms",
    "get_current_timestamp_s",
]
