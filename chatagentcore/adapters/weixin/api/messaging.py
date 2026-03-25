"""消息 API

提供消息收发、输入状态、配置获取等功能。
参考: openclaw-weixin/src/api/messaging.py
"""

import json
import uuid
from typing import Optional, List

from loguru import logger

from .client import WeixinHTTPClient
from ..constants import (
    LONG_POLL_TIMEOUT_MS,
    DEFAULT_CONFIG_TIMEOUT_MS,
    SESSION_EXPIRED_ERRCODE,
    CHANNEL_VERSION,
)
from ..models.message import (
    BaseInfo,
    MessageType,
    MessageState,
    MessageItemType,
    MessageItem,
    WeixinMessage,
    TextItem,
    GetUpdatesReq,
    GetUpdatesResp,
    SendMessageReq,
    SendMessageResp,
    SendTypingReq,
    SendTypingResp,
    GetConfigResp,
    TypingStatus,
)
from ..utils.helpers import build_base_info
from ..utils.logger import redact_token, redact_body


# ---------------------------------------------------------------------------
# 消息 API
# ---------------------------------------------------------------------------


class MessagingAPI:
    """微信消息 API

    提供消息接收（长轮询）、发送、输入状态等功能。
    """

    def __init__(
        self,
        base_url: str = "https://ilinkai.weixin.qq.com",
        token: Optional[str] = None,
        client: Optional[WeixinHTTPClient] = None,
    ):
        """初始化消息 API

        Args:
            base_url: API 基础 URL
            token: Bot Token
            client: HTTP 客户端（可选）
        """
        self.base_url = base_url
        self.token = token

        if client:
            self.client = client
        else:
            self.client = WeixinHTTPClient(base_url=base_url, token=token)

    def update_token(self, token: str) -> None:
        """更新 Token

        Args:
            token: 新的 Token
        """
        self.token = token
        self.client.update_token(token)

    def is_session_expired(self, resp: "GetUpdatesResp") -> bool:
        """检查响应是否表示会话过期

        Args:
            resp: 获取更新响应

        Returns:
            True 表示会话已过期
        """
        return resp.errcode == SESSION_EXPIRED_ERRCODE or resp.ret == SESSION_EXPIRED_ERRCODE

    async def get_updates(
        self,
        get_updates_buf: str = "",
        timeout_ms: int = LONG_POLL_TIMEOUT_MS,
    ) -> GetUpdatesResp:
        """长轮询获取消息更新

        Args:
            get_updates_buf: 上次响应返回的同步游标，首次请求传空字符串
            timeout_ms: 长轮询超时时间（毫秒）

        Returns:
            获取更新响应

        Note:
            长轮询超时是正常现象，会返回空响应（ret=0, msgs=[]）
        """
        payload = {
            "get_updates_buf": get_updates_buf,
            "base_info": build_base_info(),
        }

        try:
            logger.debug(
                f"getUpdates: buf={get_updates_buf[:50] if get_updates_buf else '(empty)'}..., timeout={timeout_ms}ms"
            )

            response_text = await self.client.post(
                "ilink/bot/getupdates",
                data=payload,
                timeout_ms=timeout_ms,
                label="getUpdates",
            )

            # 解析响应
            response_dict = json.loads(response_text)

            ret = response_dict.get("ret", 0)
            errcode = response_dict.get("errcode")
            errmsg = response_dict.get("errmsg", "")
            msgs = response_dict.get("msgs", [])
            new_buf = response_dict.get("get_updates_buf", "")
            longpolling_timeout = response_dict.get("longpolling_timeout_ms")

            logger.debug(
                f"getUpdates 响应: ret={ret}, msgs={len(msgs)}, buf={len(new_buf)} chars, timeout_hint={longpolling_timeout}"
            )

            return GetUpdatesResp(
                ret=ret,
                errcode=errcode,
                errmsg=errmsg,
                msgs=msgs,
                get_updates_buf=new_buf,
                longpolling_timeout_ms=longpolling_timeout,
            )

        except Exception as e:
            logger.error(f"getUpdates 失败: {e}")
            # 返回错误响应
            return GetUpdatesResp(ret=-1, errmsg=str(e), msgs=[], get_updates_buf=get_updates_buf)

    async def send_message(self, msg: WeixinMessage) -> None:
        """发送消息

        Args:
            msg: 要发送的微信消息

        Raises:
            Exception: 发送失败

        Note:
            收到消息时会附带 context_token，发送消息时必须携带它
        """
        # 将 Pydantic 模型序列化为字典
        msg_dict = msg.model_dump(by_alias=True, exclude_none=True)

        payload = {"msg": msg_dict, "base_info": build_base_info()}

        try:
            # 增强：输出完整的消息字典信息
            logger.debug(
                f"sendMessage: to={msg.to_user_id}, items={len(msg.item_list) if msg.item_list else 0}"
            )
            logger.debug(f"sendMessage: 序列化后的消息字典 keys={list(msg_dict.keys())}")

            # 输出关键字段用于调试
            debug_info = {
                "to_user_id": msg_dict.get("to_user_id"),
                "message_type": msg_dict.get("message_type"),
                "message_state": msg_dict.get("message_state"),
                "has_context_token": bool(msg_dict.get("context_token")),
                "context_token_prefix": msg_dict.get("context_token", "")[:20] + "..." if msg_dict.get("context_token") else None,
                "item_list_type": msg_dict.get("item_list", [{}])[0].get("type") if msg_dict.get("item_list") else None,
            }
            logger.debug(f"sendMessage: 消息详情: {debug_info}")

            response_text = await self.client.post(
                "ilink/bot/sendmessage",
                data=payload,
                timeout_ms=15000,
                label="sendMessage",
            )

            # 增强：输出 API 响应内容
            logger.debug(f"sendMessage: API 响应内容: {response_text[:200] if response_text else '(empty)'}...")
            logger.info(f"消息发送成功: to={msg.to_user_id}")

        except Exception as e:
            logger.error(f"sendMessage 失败: {e}")
            raise Exception(f"发送消息失败: {e}") from e

    async def send_text_message(
        self,
        to_user_id: str,
        text: str,
        context_token: str,
    ) -> None:
        """发送文本消息（便捷方法）

        Args:
            to_user_id: 目标用户 ID
            text: 文本内容
            context_token: 上下文令牌

        Raises:
            Exception: 发送失败
        """
        # 生成每条消息唯一的 client_id（参考 openclaw-weixin 源码）
        client_id = f"bot-{uuid.uuid4().hex[:12]}"

        msg = WeixinMessage(
            from_user_id="",  # 必需字段：标记发送方
            to_user_id=to_user_id,
            client_id=client_id,  # 必需字段：每条消息唯一 ID
            context_token=context_token,
            message_type=MessageType.BOT,
            message_state=MessageState.FINISH,
            item_list=[
                MessageItem(
                    type=MessageItemType.TEXT,
                    text_item=TextItem(text=text),
                )
            ],
        )

        await self.send_message(msg)

    async def get_config(
        self,
        ilink_user_id: str,
        context_token: Optional[str] = None,
    ) -> GetConfigResp:
        """获取账号配置（包括 typing_ticket）

        Args:
            ilink_user_id: 用户 ID
            context_token: 会话上下文令牌（可选）

        Returns:
            配置响应

        Raises:
            Exception: 获取配置失败
        """
        payload = {
            "ilink_user_id": ilink_user_id,
            "context_token": context_token,
            "base_info": build_base_info(),
        }

        try:
            response_text = await self.client.post(
                "ilink/bot/getconfig",
                data=payload,
                timeout_ms=DEFAULT_CONFIG_TIMEOUT_MS,
                label="getConfig",
            )

            response_dict = json.loads(response_text)

            return GetConfigResp(
                ret=response_dict.get("ret", 0),
                errmsg=response_dict.get("errmsg", ""),
                typing_ticket=response_dict.get("typing_ticket", ""),
            )

        except Exception as e:
            logger.error(f"getConfig 失败: {e}")
            raise Exception(f"获取配置失败: {e}") from e

    async def send_typing(
        self,
        ilink_user_id: str,
        typing_ticket: str,
        status: int = TypingStatus.TYPING,
    ) -> None:
        """发送或取消输入状态指示

        Args:
            ilink_user_id: 用户 ID
            typing_ticket: 输入状态票据（从 getConfig 获取）
            status: 状态值（1=正在输入, 2=取消输入）

        Raises:
            Exception: 发送状态失败
        """
        payload = {
            "ilink_user_id": ilink_user_id,
            "typing_ticket": typing_ticket,
            "status": status,
            "base_info": build_base_info(),
        }

        try:
            await self.client.post(
                "ilink/bot/sendtyping",
                data=payload,
                timeout_ms=DEFAULT_CONFIG_TIMEOUT_MS,
                label="sendTyping",
            )

            logger.debug(f"输入状态已发送: user={ilink_user_id}, status={status}")

        except Exception as e:
            logger.error(f"sendTyping 失败: {e}")
            raise Exception(f"发送输入状态失败: {e}") from e

    async def send_typing_start(
        self,
        ilink_user_id: str,
        typing_ticket: str,
    ) -> None:
        """开始输入状态

        Args:
            ilink_user_id: 用户 ID
            typing_ticket: 输入状态票据
        """
        await self.send_typing(ilink_user_id, typing_ticket, TypingStatus.TYPING)

    async def send_typing_cancel(
        self,
        ilink_user_id: str,
        typing_ticket: str,
    ) -> None:
        """取消输入状态

        Args:
            ilink_user_id: 用户 ID
            typing_ticket: 输入状态票据
        """
        await self.send_typing(ilink_user_id, typing_ticket, TypingStatus.CANCEL)

    async def close(self) -> None:
        """关闭客户端"""
        await self.client.close()
