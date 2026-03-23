"""微信适配器

基于 iLink AI 微信聊天 API 的完整实现。
继承自 BaseAdapter，提供统一的接口。

主要功能：
- 扫码登录
- 长轮询接收消息
- 发送文本/图片/视频/文件/语音消息
- 媒体文件上传下载
- 输入状态指示
- 会话管理
"""

import asyncio
from typing import Any, Callable, Optional, Dict

from loguru import logger

# 使用相对导入（更健壮）
from chatagentcore.adapters.base import BaseAdapter, Message

# 导入微信适配器组件
from .api.auth import AuthAPI
from .api.messaging import MessagingAPI
from .api.media import MediaAPI
from .storage.token_store import TokenStore
from .storage.sync_buf import SyncBufStore
from .context.cache import ContextCache

from .models.message import (
    MessageItemType,
    MessageItem,
    WeixinMessage,
    TextItem,
    ImageItem,
)
from .models.auth import DEFAULT_ILINK_BOT_TYPE
from .constants import (
    DEFAULT_BASE_URL as _DEFAULT_BASE_URL,
    DEFAULT_CDN_BASE_URL as _DEFAULT_CDN_BASE_URL,
    LONG_POLL_TIMEOUT_MS,
    SESSION_PAUSE_MS,
)


# ---------------------------------------------------------------------------
# 常量导出
# ---------------------------------------------------------------------------

DEFAULT_BASE_URL = _DEFAULT_BASE_URL
DEFAULT_CDN_BASE_URL = _DEFAULT_CDN_BASE_URL


# ---------------------------------------------------------------------------
# 主适配器
# ---------------------------------------------------------------------------


class WeixinAdapter(BaseAdapter):
    """微信适配器

    通过 iLink AI 微信聊天 API 提供完整的微信聊天功能。
    """

    def __init__(self, config: Dict[str, Any]):
        """初始化微信适配器

        Args:
            config: 平台配置
                {
                    "account_id": "账号 ID",
                    "base_url": "API 基础 URL",
                    "cdn_base_url": "CDN 基础 URL",
                    "token": "Bot Token（可选，可从文件加载）",
                    "state_dir": "状态目录（可选）",
                }
        """
        super().__init__(config)

        # 基础配置
        self.account_id = config.get("account_id", "")
        self.base_url = config.get("base_url", DEFAULT_BASE_URL)
        self.cdn_base_url = config.get("cdn_base_url", DEFAULT_CDN_BASE_URL)
        self.state_dir = config.get("state_dir")

        # Token
        self.token = config.get("token")

        # 组件
        self.auth_api: Optional[AuthAPI] = None
        self.messaging_api: Optional[MessagingAPI] = None
        self.media_api: Optional[MediaAPI] = None
        self.token_store = TokenStore(self.state_dir)
        self.sync_buf_store = SyncBufStore(self.state_dir)
        self.context_cache = ContextCache()

        # 运行状态
        self._running = False
        self._message_handlers = []
        self._long_poll_task: Optional[asyncio.Task] = None

        # 会话管理
        self._session_paused_until = 0

    async def initialize(self) -> None:
        """初始化适配器"""
        logger.info(f"初始化微信适配器: account_id={self.account_id}, base_url={self.base_url}")

        # 尝试从 TokenStore 加载 Token
        if not self.token:
            loaded_token = self.token_store.get_token(self.account_id)
            if loaded_token:
                self.token = loaded_token
                logger.info(f"从存储加载 Token: {self._redact_token()}")

        # 初始化 API 客户端
        if self.token:
            self.auth_api = AuthAPI(base_url=self.base_url)
            self.messaging_api = MessagingAPI(
                base_url=self.base_url, token=self.token
            )
            self.media_api = MediaAPI(
                base_url=self.base_url,
                cdn_base_url=self.cdn_base_url,
                token=self.token,
            )

            # 启动长轮询
            self._running = True
            self._long_poll_task = asyncio.create_task(self._long_poll_loop())
            logger.info("微信适配器初始化完成：已启动长轮询")
        else:
            logger.warning("微信 Token 未配置，请先调用 login_with_qr() 进行扫码登录")

    async def shutdown(self) -> None:
        """关闭适配器"""
        logger.info("关闭微信适配器")

        self._running = False

        # 取消长轮询任务
        if self._long_poll_task:
            self._long_poll_task.cancel()
            try:
                await self._long_poll_task
            except asyncio.CancelledError:
                pass

        # 关闭 API 客户端
        if self.auth_api:
            await self.auth_api.close()
        if self.messaging_api:
            await self.messaging_api.close()
        if self.media_api:
            await self.media_api.close()

        logger.info("微信适配器已关闭")

    async def health_check(self) -> bool:
        """健康检查"""
        return self._running and self.token is not None

    def set_message_handler(self, handler: Callable[[Message], None]):
        """设置消息处理器"""
        self._message_handlers.append(handler)

    # -----------------------------------------------------------------------
    # 登录功能
    # -----------------------------------------------------------------------

    async def login_with_qr(
        self,
        timeout_ms: int = 300000,
        display_callback: Optional[Callable[[str], None]] = None,
    ) -> Dict[str, Any]:
        """扫码登录

        Args:
            timeout_ms: 超时时间（毫秒），默认 5 分钟
            display_callback: 二维码显示回调函数

        Returns:
            登录结果字典
            {
                "success": bool,
                "message": str,
                "bot_token": str,
                "account_id": str,
                "user_id": str,
            }
        """
        logger.info("启动微信扫码登录...")

        # 显示回调：默认使用终端显示
        if display_callback is None:
            from .utils.qr import display_qrcode_terminal
            display_callback = display_qrcode_terminal

        # 创建 AuthAPI
        self.auth_api = AuthAPI(base_url=self.base_url)

        # 执行登录
        result = await self.auth_api.login_with_qr(
            timeout_ms=timeout_ms,
            display_callback=display_callback,
        )

        if result.success:
            # 保存 Token
            self.token = result.bot_token
            self.token_store.save(
                account_id=result.account_id or self.account_id,
                token=self.token,
                base_url=result.base_url or self.base_url,
                user_id=result.user_id,
            )

            # 更新 account_id
            if result.account_id:
                self.account_id = result.account_id

            # 初始化 API
            self.messaging_api = MessagingAPI(
                base_url=self.base_url, token=self.token
            )
            self.media_api = MediaAPI(
                base_url=self.base_url,
                cdn_base_url=self.cdn_base_url,
                token=self.token,
            )

            # 启动长轮询
            if not self._running:
                self._running = True
                self._long_poll_task = asyncio.create_task(self._long_poll_loop())

            return {
                "success": True,
                "message": result.message,
                "bot_token": result.bot_token,
                "account_id": result.account_id,
                "user_id": result.user_id,
            }

        else:
            return {
                "success": False,
                "message": result.message,
            }

    # -----------------------------------------------------------------------
    # 消息发送
    # -----------------------------------------------------------------------

    async def send_message(
        self,
        to: str,
        message_type: str,
        content: Any,
        conversation_type: str = "user",
    ) -> str:
        """发送消息（继承自 BaseAdapter）

        Args:
            to: 接收者 ID
            message_type: 消息类型
            content: 消息内容
            conversation_type: 会话类型

        Returns:
            发送后的消息 ID

        Raises:
            Exception: 发送失败或未登录
        """
        if not self.messaging_api:
            raise Exception("微信适配器未初始化，请先登录")

        # 获取 context_token
        context_token = self.context_cache.get(to)
        if not context_token:
            raise Exception(
                f"未找到上下文令牌，请先接收来自 {to} 的消息（会话未建立）"
            )

        # 处理不同的消息类型
        if message_type == "text":
            await self.messaging_api.send_text_message(
                to_user_id=to, text=str(content), context_token=context_token
            )
        else:
            # 默认作为文本发送
            await self.messaging_api.send_text_message(
                to_user_id=to, text=str(content), context_token=context_token
            )

        # 返回消息 ID（格式：wx_timestamp）
        message_id = f"wx_{self._get_current_timestamp_ms()}"
        return message_id

    async def send_text_message(
        self,
        to: str,
        text: str,
    ) -> str:
        """发送文本消息（便捷方法）

        Args:
            to: 接收者 ID
            text: 文本内容

        Returns:
            发送后的消息 ID
        """
        return await self.send_message(to, "text", text)

    async def send_media_message(
        self,
        to: str,
        media_path: str,
        caption: str = "",
        thumbnail_path: Optional[str] = None,
    ) -> str:
        """发送媒体消息（图片、视频、文件）

        Args:
            to: 接收者 ID
            media_path: 媒体文件路径
            caption: 附带文本
            thumbnail_path: 缩略图路径（可选）

        Returns:
            发送后的消息 ID

        Raises:
            Exception: 发送失败
        """
        if not self.media_api:
            raise Exception("媒体 API 未初始化")

        # 获取 context_token
        from_user_id = to  # 发送给的用户就是 context_token 的使用者
        context_token = self.context_cache.get(from_user_id)
        if not context_token:
            # 尝试互换：接收消息时的 from_user_id 可能是发送的目标
            context_token = self.context_cache.get(to)
            if not context_token:
                raise Exception(
                    f"未找到上下文令牌，请先接收来自 {to} 的消息（会话未建立）"
                )

        # 确定媒体类型
        import os

        ext = os.path.splitext(media_path)[1].lower()
        if ext in (".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"):
            media_type = 1
        elif ext in (".mp4", ".avi", ".mov", ".mkv", ".flv"):
            media_type = 2
        else:
            media_type = 3

        # 上传媒体
        media_ref = await self.media_api.upload_media(
            file_path=media_path,
            to_user_id=to,
            media_type=media_type,
            thumbnail_path=thumbnail_path,
        )

        # 发送消息
        msg = WeixinMessage(
            to_user_id=to,
            context_token=context_token,
            item_list=[
                MessageItem(
                    type=media_type,
                    image_item=ImageItem(media=media_ref) if media_type == 1 else None,
                )
            ],
        )

        await self.messaging_api.send_message(msg)

        return f"wx_{self._get_current_timestamp_ms()}"

    # -----------------------------------------------------------------------
    # 消息接收
    # -----------------------------------------------------------------------

    async def _long_poll_loop(self):
        """长轮询主循环"""
        logger.info("微信长轮询已启动")

        # 加载上次保存的游标
        sync_buf = self.sync_buf_store.load(self.account_id) or ""

        consecutive_failures = 0
        max_consecutive_failures = 3

        while self._running:
            # 检查会话是否暂停
            if time.time() * 1000 < self._session_paused_until:
                import time as _time

                wait_ms = self._session_paused_until - _time.time() * 1000
                logger.debug(f"会话已暂停，等待 {wait_ms/1000:.0f} 秒")
                await asyncio.sleep(min(5, wait_ms / 1000))
                continue

            try:
                # 长轮询接收消息
                resp = await self.messaging_api.get_updates(
                    get_updates_buf=sync_buf, timeout_ms=LONG_POLL_TIMEOUT_MS
                )

                # 重置失败计数
                consecutive_failures = 0

                # 检查会话过期
                if self.messaging_api.is_session_expired(resp):
                    logger.warning("会话已过期，暂停 5 分钟")
                    import time as _time

                    self._session_paused_until = _time.time() * 1000 + SESSION_PAUSE_MS
                    continue

                # 检查 API 错误
                if resp.ret != 0:
                    logger.error(
                        f"getUpdates 失败: ret={resp.ret}, errcode={resp.errcode}, errmsg={resp.errmsg}"
                    )
                    consecutive_failures += 1
                    if consecutive_failures >= max_consecutive_failures:
                        logger.warning(f"连续 {max_consecutive_failures} 次失败，等待 30 秒")
                        await asyncio.sleep(30)
                    else:
                        await asyncio.sleep(2)
                    continue

                # 保存新游标
                if resp.get_updates_buf:
                    self.sync_buf_store.save(self.account_id, resp.get_updates_buf)
                    sync_buf = resp.get_updates_buf

                # 处理消息
                if resp.msgs:
                    for wx_msg in resp.msgs:
                        await self._handle_message(wx_msg)

            except asyncio.CancelledError:
                logger.info("长轮询已取消")
                break
            except Exception as e:
                logger.error(f"长轮询异常: {e}")
                consecutive_failures += 1
                if consecutive_failures >= max_consecutive_failures:
                    await asyncio.sleep(30)
                else:
                    await asyncio.sleep(2)

        logger.info("微信长轮询已停止")

    async def _handle_message(self, wx_msg: WeixinMessage):
        """处理单条微信消息"""
        # 提取文本内容
        text = ""
        has_media = False
        media_info = {}

        if wx_msg.item_list:
            for item in wx_msg.item_list:
                if item.type == MessageItemType.TEXT and item.text_item and item.text_item.text:
                    text = item.text_item.text
                elif item.type in (MessageItemType.IMAGE, MessageItemType.VIDEO, MessageItemType.FILE, MessageItemType.VOICE):
                    has_media = True
                    media_info["type"] = item.type

        # 缓存 context_token
        if wx_msg.to_user_id and wx_msg.context_token:
            self.context_cache.set(
                to_user_id=wx_msg.to_user_id, context_token=wx_msg.context_token
            )

        # 转换为统一 Message 格式
        msg = Message(
            platform="weixin",
            message_id=str(wx_msg.message_id),
            sender={"id": wx_msg.from_user_id or "", "name": ""},
            conversation={"id": wx_msg.session_id or "", "type": "user"},
            content={
                "type": "text",
                "text": text,
                "has_media": has_media,
                "media": media_info,
            },
            timestamp=wx_msg.create_time_ms // 1000 if wx_msg.create_time_ms else self._get_current_timestamp_s(),
        )

        # 分发给处理器
        for handler in self._message_handlers:
            try:
                handler(msg)
            except Exception as e:
                logger.error(f"消息处理器异常: {e}")

    # -----------------------------------------------------------------------
    # 辅助方法
    # -----------------------------------------------------------------------

    def _redact_token(self) -> str:
        """Token 脱敏"""
        if not self.token:
            return "(none)"
        if len(self.token) <= 12:
            return self.token[:4] + "..."
        return self.token[:8] + "..." + self.token[-4:]

    @staticmethod
    def _get_current_timestamp_ms() -> int:
        """获取当前时间戳（毫秒）"""
        import time
        return int(time.time() * 1000)

    @staticmethod
    def _get_current_timestamp_s() -> int:
        """获取当前时间戳（秒）"""
        import time
        return int(time.time())
