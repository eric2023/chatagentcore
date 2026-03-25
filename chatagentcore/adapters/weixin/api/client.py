"""HTTP 客户端基类

封装通用的 HTTP 请求逻辑，包括认证、重试、超时等。
参考: openclaw-weixin/src/api/api.ts
"""

import asyncio
import json
from typing import Optional, Dict, Any

import httpx
from loguru import logger

from ..models.message import BaseInfo
from ..constants import (
    DEFAULT_BASE_URL,
    DEFAULT_CDN_BASE_URL,
    LONG_POLL_TIMEOUT_MS,
    DEFAULT_API_TIMEOUT_MS,
    DEFAULT_CONFIG_TIMEOUT_MS,
    SESSION_EXPIRED_ERRCODE,
    MAX_CONSECUTIVE_FAILURES,
    BACKOFF_DELAY_MS,
    RETRY_DELAY_MS,
    CHANNEL_VERSION,
)


# ---------------------------------------------------------------------------
# HTTP 客户端
# ---------------------------------------------------------------------------

class WeixinHTTPClient:
    """微信 HTTP 客户端基类

    封装了通用的 HTTP 请求逻辑，包括认证 Headers、重试机制等。
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        token: Optional[str] = None,
        route_tag: Optional[str] = None,
    ):
        """初始化 HTTP 客户端

        Args:
            base_url: API 基础 URL
            token: Bot Token（可选）
            route_tag: 路由标签（可选）
        """
        # 确保 base_url 以 / 结尾
        self.base_url = base_url.rstrip('/') + '/'
        self.token = token
        self.route_tag = route_tag
        self._client: Optional[httpx.AsyncClient] = None

    def update_token(self, token: str) -> None:
        """更新 Token

        Args:
            token: 新的 Token
        """
        self.token = token

    def update_route_tag(self, route_tag: str) -> None:
        """更新路由标签

        Args:
            route_tag: 新的路由标签
        """
        self.route_tag = route_tag

    async def _get_client(self) -> httpx.AsyncClient:
        """获取或创建 HTTP 客户端

        Returns:
            httpx.AsyncClient 实例
        """
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=httpx.Timeout(DEFAULT_API_TIMEOUT_MS))
        return self._client

    async def close(self) -> None:
        """关闭 HTTP 客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None

    def build_url(self, endpoint: str) -> str:
        """构建完整的请求 URL

        Args:
            endpoint: API 端点（如 "ilink/bot/getupdates"）

        Returns:
            完整 URL
        """
        # 确保 base_url 以 / 结尾，endpoint 不要以 / 开头
        clean_endpoint = endpoint.lstrip('/')
        return self.base_url + clean_endpoint

    def _build_headers(self) -> Dict[str, str]:
        """构建请求 Headers

        Returns:
            Headers 字典
        """
        import base64
        import secrets

        headers = {
            "Content-Type": "application/json",
            "AuthorizationType": "ilink_bot_token",
            "X-WECHAT-UIN": self._generate_random_uin(),
        }

        if self.token and self.token.strip():
            headers["Authorization"] = f"Bearer {self.token.strip()}"

        if self.route_tag:
            headers["SKRouteTag"] = str(self.route_tag)

        return headers

    def _generate_random_uin(self) -> str:
        """生成随机 UIN

        Returns:
            base64 编码的 UIN
        """
        import base64
        import secrets

        uint32 = secrets.randbelow(2**32)
        uin_string = str(uint32)
        return base64.b64encode(uin_string.encode('utf-8')).decode('utf-8')

    def _redact_token(self) -> str:
        """Token 脱敏

        Returns:
            脱敏后的字符串
        """
        if not self.token:
            return "(none)"
        if len(self.token) <= 12:
            return self.token[:4] + "..."
        return self.token[:8] + "..." + self.token[-4:]

    def _redact_body(self, body: str, max_length: int = 200) -> str:
        """Body 脱敏

        Args:
            body: 原始内容
            max_length: 截断长度

        Returns:
            脱敏后的字符串
        """
        if len(body) > max_length:
            return body[:max_length] + f"... ({len(body)} chars)"
        return body

    async def _request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        timeout_ms: int = DEFAULT_API_TIMEOUT_MS,
        label: str = "",
    ) -> str:
        """执行 HTTP 请求（底层方法）

        Args:
            method: HTTP 方法（"GET" 或 "POST"）
            endpoint: API 端点（如 "ilink/bot/getupdates"）
            data: 请求体数据（POST 用）
            params: 查询参数（GET 用）
            timeout_ms: 超时时间（毫秒）
            label: 请求标签（用于日志）

        Returns:
            响应文本

        Raises:
            httpx.HTTPError: 请求失败
        """
        url = self.build_url(endpoint)
        client = await self._get_client()

        # 构建请求 Headers
        headers = self._build_headers()

        # 序列化请求体
        body_str = ""
        if data is not None:
            # 添加 channel_version
            if "base_info" not in data:
                data["base_info"] = {"channel_version": CHANNEL_VERSION}
            body_str = json.dumps(data, ensure_ascii=False, separators=(',', ':'))

        logger.debug(f"[{label}] HTTP {method} {url}")
        logger.debug(f"[{label}] Token: {self._redact_token()}")
        if body_str:
            logger.debug(f"[{label}] Body: {self._redact_body(body_str)}")

        # 设置超时
        timeout = httpx.Timeout(timeout_ms / 1000.0)

        try:
            if method == "POST":
                response = await client.post(url, json=data, headers=headers, timeout=timeout)
            elif method == "GET":
                response = await client.get(url, params=params, headers=headers, timeout=timeout)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")

            logger.debug(f"[{label}] Response: status={response.status_code}")

            # 增强：输出响应内容（特别是 sendMessage）
            response_text = response.text
            if "sendMessage" in label or response_text:
                # 对于 sendMessage 请求，输出完整响应以便调试
                preview = response_text[:300] if response_text else "(empty)"
                logger.debug(f"[{label}] Response body: {preview}{'...' if len(response_text) > 300 else ''}")

            # 检查响应状态
            if not response.is_success:
                error_text = response.text
                logger.error(f"[{label}] HTTP Error {response.status_code}: {error_text}")
                # 某些 API 失败返回 JSON
                try:
                    error_json = self._parse_json(error_text)
                    errcode = error_json.get("errcode")
                    errmsg = error_json.get("errmsg", error_text)
                    raise httpx.HTTPStatusError(
                        f"API Error: errcode={errcode}, errmsg={errmsg}",
                        request=response.request,
                        response=response,
                    )
                except ValueError:
                    raise httpx.HTTPStatusError(
                        f"HTTP Error {response.status_code}: {error_text}",
                        request=response.request,
                        response=response,
                    )

            return response.text

        except httpx.TimeoutException as e:
            logger.debug(f"[{label}] Timeout after {timeout_ms}ms")
            raise
        except httpx.HTTPError as e:
            logger.error(f"[{label}] HTTP Error: {e}")
            raise

    def _parse_json(self, text: str) -> Any:
        """安全的 JSON 解析

        Args:
            text: JSON 字符串

        Returns:
            解析后的对象

        Raises:
            ValueError: JSON 解析失败
        """
        try:
            return json.loads(text)
        except json.JSONDecodeError as e:
            error_msg = f"JSON 解析失败: {e}"
            logger.debug(f"{error_msg}, 原始文本: {text[:500]}...")
            raise ValueError(error_msg) from e

    async def post(
        self,
        endpoint: str,
        data: Dict[str, Any],
        timeout_ms: int = DEFAULT_API_TIMEOUT_MS,
        label: str = "POST",
    ) -> str:
        """执行 POST 请求

        Args:
            endpoint: API 端点
            data: 请求体数据
            timeout_ms: 超时时间（毫秒）
            label: 请求标签

        Returns:
            响应文本
        """
        return await self._request("POST", endpoint, data=data, timeout_ms=timeout_ms, label=label)

    async def get(
        self,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        timeout_ms: int = DEFAULT_API_TIMEOUT_MS,
        label: str = "GET",
    ) -> str:
        """执行 GET 请求

        Args:
            endpoint: API 端点
            params: 查询参数
            timeout_ms: 超时时间（毫秒）
            label: 请求标签

        Returns:
            响应文本
        """
        return await self._request("GET", endpoint, params=params, timeout_ms=timeout_ms, label=label)


# ---------------------------------------------------------------------------
# 工厂函数
# ---------------------------------------------------------------------------

def create_http_client(
    base_url: str = DEFAULT_BASE_URL,
    token: Optional[str] = None,
) -> WeixinHTTPClient:
    """创建 HTTP 客户端

    Args:
        base_url: API 基础 URL
        token: Bot Token

    Returns:
        WeixinHTTPClient 实例
    """
    return WeixinHTTPClient(base_url=base_url, token=token)
