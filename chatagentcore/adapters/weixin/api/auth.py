"""认证 API

提供扫码登录相关功能。
参考: openclaw-weixin/src/auth/login-qr.ts
"""

import asyncio
import time
import uuid
from typing import Optional

import httpx
from loguru import logger

from .client import WeixinHTTPClient, DEFAULT_BASE_URL
from ..models.auth import QrcodeResponse, QrcodeStatus, LoginResult, DEFAULT_ILINK_BOT_TYPE
from ..utils.logger import redact_token


# ---------------------------------------------------------------------------
# 认证 API
# ---------------------------------------------------------------------------


class AuthAPI:
    """微信认证 API

    提供扫码登录功能。
    """

    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        client: Optional[WeixinHTTPClient] = None,
    ):
        """初始化认证 API

        Args:
            base_url: API 基础 URL
            client: HTTP 客户端（可选，未提供时自动创建）
        """
        self.base_url = base_url
        self.client = client or WeixinHTTPClient(base_url=base_url)

        # 管理活跃的登录会话
        self._active_logins: dict[str, dict] = {}

    def _create_login_session(self, session_key: str, qrcode: str, qrcode_url: str) -> None:
        """创建登录会话

        Args:
            session_key: 会话密钥
            qrcode: 二维码内容
            qrcode_url: 二维码图片 URL
        """
        self._active_logins[session_key] = {
            "session_key": session_key,
            "qrcode": qrcode,
            "qrcode_url": qrcode_url,
            "started_at": time.time(),
            "status": "wait",
        }

        # 清理过期会话（5 分钟）
        self._purge_expired_logins()

    def _get_login_session(self, session_key: str) -> Optional[dict]:
        """获取登录会话

        Args:
            session_key: 会话密钥

        Returns:
            登录会话数据，不存在返回 None
        """
        session = self._active_logins.get(session_key)
        if not session:
            return None

        # 检查是否过期
        if time.time() - session["started_at"] > 5 * 60_000:
            self._active_logins.pop(session_key, None)
            return None

        return session

    def _update_login_session(self, session_key: str, **kwargs) -> None:
        """更新登录会话

        Args:
            session_key: 会话密钥
            **kwargs: 要更新的字段
        """
        if session_key in self._active_logins:
            self._active_logins[session_key].update(kwargs)

    def _purge_expired_logins(self) -> None:
        """清理过期的登录会话"""
        current_time = time.time()
        expired_keys = [
            key
            for key, data in self._active_logins.items()
            if current_time - data["started_at"] > 5 * 60_000
        ]
        for key in expired_keys:
            del self._active_logins[key]

    async def get_bot_qrcode(
        self,
        bot_type: str = DEFAULT_ILINK_BOT_TYPE,
    ) -> QrcodeResponse:
        """获取登录二维码

        Args:
            bot_type: Bot 类型（默认 "3"）

        Returns:
            二维码响应

        Raises:
            Exception: 获取二维码失败
        """
        session_key = str(uuid.uuid4())
        url = f"ilink/bot/get_bot_qrcode?bot_type={bot_type}"

        try:
            logger.info(f"获取微信登录二维码: bot_type={bot_type}")

            # GET 请求获取二维码
            response_text = await self.client.get(url, label="get_bot_qrcode")

            # 解析响应
            response_dict = {}
            try:
                import json

                response_dict = json.loads(response_text)
            except Exception:
                # 如果解析失败，可能是直接返回的格式
                pass

            qrcode = response_dict.get("qrcode", "")
            qrcode_img_content = response_dict.get("qrcode_img_content", "")
            qrcode_url = qrcode_img_content or qrcode

            logger.info(f"二维码获取成功: qrcode={qrcode[:20]}..., img_url={qrcode_url[:50] if qrcode_url else '(none)'}...")

            # 创建登录会话
            self._create_login_session(session_key, qrcode, qrcode_url)

            return QrcodeResponse(qrcode=qrcode, qrcode_img_content=qrcode_url)

        except httpx.HTTPError as e:
            logger.error(f"获取二维码失败: {e}")
            raise Exception(f"获取二维码失败: {e}") from e

    async def get_qrcode_status(
        self,
        qrcode: Optional[str] = None,
        session_key: Optional[str] = None,
        timeout_ms: int = 35000,
    ) -> QrcodeStatus:
        """轮询二维码状态（长轮询）

        Args:
            qrcode: 二维码内容（可选）
            session_key: 会话密钥（可选，用于自动获取 qrcode）
            timeout_ms: 超时时间（毫秒）

        Returns:
            二维码状态

        Raises:
            Exception: 查询状态失败
        """
        # 如果提供了 session_key，自动获取 qrcode
        if session_key and not qrcode:
            session = self._get_login_session(session_key)
            if session:
                qrcode = session["qrcode"]
            else:
                return QrcodeStatus(status="expired")

        if not qrcode:
            raise ValueError("必须提供 qrcode 或 session_key")

        url = f"ilink/bot/get_qrcode_status?qrcode={qrcode}"

        try:
            # 使用指定的超时时间
            headers = {"iLink-App-ClientVersion": "1"}

            # 直接使用 httpx 实现长轮询
            client = await self.client._get_client()
            full_url = self.client.build_url(url)

            logger.debug(f"轮询二维码状态: qrcode={qrcode[:20]}...")

            response = await client.get(
                full_url,
                headers=headers,
                timeout=httpx.Timeout(timeout_ms / 1000.0),
            )

            if not response.is_success:
                logger.error(f"查询二维码状态失败: {response.status_code}")
                raise Exception(f"查询二维码状态失败: {response.status_code}")

            response_dict = response.json()
            status = response_dict.get("status", "wait")

            logger.debug(f"二维码状态: {status}")

            return QrcodeStatus(
                status=status,
                bot_token=response_dict.get("bot_token"),
                ilink_bot_id=response_dict.get("ilink_bot_id"),
                baseurl=response_dict.get("baseurl"),
                ilink_user_id=response_dict.get("ilink_user_id"),
            )

        except httpx.TimeoutException:
            # 长轮询超时是正常的，返回 wait 状态
            logger.debug("二维码状态查询超时（正常，长轮询）")
            return QrcodeStatus(status="wait")
        except httpx.HTTPError as e:
            logger.error(f"查询二维码状态失败: {e}")
            raise Exception(f"查询二维码状态失败: {e}") from e

    async def wait_for_qrcode_scan(
        self,
        qrcode_response: QrcodeResponse,
        timeout_ms: int = 300000,
        refresh_on_expired: bool = True,
        max_refresh_count: int = 3,
    ) -> LoginResult:
        """等待二维码扫码（轮询直到确认或超时）

        Args:
            qrcode_response: 二维码响应
            timeout_ms: 超时时间（毫秒，默认 5 分钟）
            refresh_on_expired: 过期时是否自动刷新二维码
            max_refresh_count: 最大刷新次数

        Returns:
            登录结果
        """
        qrcode = qrcode_response.qrcode
        qrcode_url = qrcode_response.qrcode_img_content or ""
        start_time = time.time()
        deadline = start_time + timeout_ms / 1000.0
        refresh_count = 0
        scanned_printed = False

        logger.info("等待二维码扫码...")

        while time.time() < deadline:
            try:
                # 轮询二维码状态
                status_resp = await self.get_qrcode_status(qrcode=qrcode)

                if status_resp.status == "wait":
                    pass  # 继续等待

                elif status_resp.status == "scaned":
                    if not scanned_printed:
                        print("\n已扫码，请在微信中确认登录...")
                        scanned_printed = True

                elif status_resp.status == "confirmed":
                    # 登录成功
                    bot_token = status_resp.bot_token
                    ilink_bot_id = status_resp.ilink_bot_id
                    base_url = status_resp.baseurl
                    user_id = status_resp.ilink_user_id

                    if not bot_token or not ilink_bot_id:
                        logger.error("登录确认但缺少必要信息")
                        return LoginResult(
                            success=False,
                            message="登录失败：服务器未返回必要信息",
                        )

                    logger.info(
                        f"登录成功: bot_id={ilink_bot_id}, user_id={user_id}, token={redact_token(bot_token)}"
                    )

                    return LoginResult(
                        success=True,
                        message="登录成功",
                        bot_token=bot_token,
                        account_id=ilink_bot_id,
                        base_url=base_url or self.base_url,
                        user_id=user_id,
                    )

                elif status_resp.status == "expired":
                    # 二维码过期
                    if refresh_on_expired and refresh_count < max_refresh_count:
                        refresh_count += 1
                        print(f"\n二维码已过期，正在刷新 ({refresh_count}/{max_refresh_count})...")
                        logger.info(f"二维码过期，刷新 ({refresh_count}/{max_refresh_count})")

                        try:
                            # 重新获取二维码
                            new_qr_resp = await self.get_bot_qrcode()
                            qrcode = new_qr_resp.qrcode
                            qrcode_url = new_qr_resp.qrcode_img_content or ""
                            scanned_printed = False
                            print("\n新二维码已生成，请重新扫描")
                        except Exception as e:
                            logger.error(f"刷新二维码失败: {e}")
                            return LoginResult(success=False, message=f"刷新二维码失败: {e}")
                    else:
                        logger.error(f"二维码多次过期 ({refresh_count} 次)，放弃")
                        return LoginResult(
                            success=False, message="登录超时：二维码多次过期，请重试"
                        )

                # 等待 1 秒后继续轮询
                await asyncio.sleep(1)

            except Exception as e:
                logger.error(f"轮询二维码状态异常: {e}")
                await asyncio.sleep(2)

        # 超时
        logger.error(f"等待扫码超时: {timeout_ms}ms")
        return LoginResult(success=False, message="登录超时，请重试")

    async def login_with_qr(
        self,
        bot_type: str = DEFAULT_ILINK_BOT_TYPE,
        timeout_ms: int = 300000,
        display_callback=None,
    ) -> LoginResult:
        """完整的扫码登录流程

        Args:
            bot_type: Bot 类型
            timeout_ms: 超时时间（毫秒）
            display_callback: 二维码显示回调函数

        Returns:
            登录结果
        """
        try:
            # 1. 获取二维码
            logger.info("启动微信扫码登录...")
            qrcode_response = await self.get_bot_qrcode(bot_type=bot_type)

            if not qrcode_response.qrcode:
                return LoginResult(success=False, message="获取二维码失败")

            # 2. 显示二维码
            if display_callback:
                display_callback(qrcode_response.qrcode_img_content or qrcode_response.qrcode)
            else:
                # 默认显示：打印 URL
                print("\n请使用微信扫描以下二维码完成登录：")
                print("-" * 50)
                if qrcode_response.qrcode_img_content:
                    print(f"二维码链接: {qrcode_response.qrcode_img_content}")
                else:
                    print(f"二维码内容: {qrcode_response.qrcode}")
                print("-" * 50)
                print()

            # 3. 等待扫码
            result = await self.wait_for_qrcode_scan(qrcode_response, timeout_ms=timeout_ms)

            return result

        except Exception as e:
            logger.error(f"扫码登录失败: {e}")
            return LoginResult(success=False, message=f"扫码登录失败: {e}")

    async def close(self) -> None:
        """关闭客户端"""
        await self.client.close()
