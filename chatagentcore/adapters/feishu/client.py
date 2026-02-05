"""飞书适配器客户端 - 支持官方 SDK 长连接 (WebSocket) 方式

基于飞书官方 Python SDK (lark_oapi)，通过 WebSocket 长连接接收消息。
"""

import json
import asyncio
import time
import httpx
import threading
from typing import Optional, Dict, Any, Callable, Awaitable
from loguru import logger

# 优先导入 WS 客户端（长连接）
try:
    from lark_oapi.ws import Client as WSClient
    from lark_oapi.event.dispatcher_handler import EventDispatcherHandler
    from lark_oapi.core.enum import LogLevel
    from lark_oapi.core.const import FEISHU_DOMAIN, LARK_DOMAIN
    HAS_WS_CLIENT = True
except ImportError:
    HAS_WS_CLIENT = False

try:
    from lark_oapi import Client
    HAS_SDK = True
except ImportError:
    HAS_SDK = False
    logger.warning("lark_oapi SDK 未安装，请运行: pip install lark_oapi")


# 域名映射
_DOMAIN_MAP = {
    "feishu": FEISHU_DOMAIN,
    "lark": LARK_DOMAIN,
}


def _resolve_domain(domain: str) -> str:
    """解析域名为完整 URL"""
    return _DOMAIN_MAP.get(domain, FEISHU_DOMAIN)


def _run_in_thread(loop: asyncio.AbstractEventLoop, coro):
    """在新线程中运行异步任务"""
    asyncio.set_event_loop(loop)
    loop.run_until_complete(coro)


def _run_ws_in_new_thread(ws_client: WSClient):
    """
    在独立线程中运行 WebSocket 客户端

    创建新的事件循环以避免与主线程/主应用的 event loop 冲突。

    注意：lark_oapi.ws.client 模块级全局 loop 需要重置。
    """
    # 新线程开始时，首先清除可能存在的全局 loop
    # lark_oapi.ws.client 在模块导入时设置了全局 loop

    # 主动设置当前线程的 loop 为 None，强制 asyncio 创建新的
    try:
        asyncio.get_event_loop()
        asyncio.set_event_loop(None)
    except RuntimeError:
        # 没有当前事件循环，这是正常的
        pass

    # 创建新的事件循环
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # 重置 lark_oapi.ws.client 模块的全局 loop 变量
    try:
        from lark_oapi.ws import client as ws_client_module
        if hasattr(ws_client_module, 'loop'):
            ws_client_module.loop = loop
    except Exception as e:
        logger.debug(f"无法重置 SDK 模块 loop: {e}")

    try:
        # 在新的事件循环中运行 WebSocket 客户端
        # 注意：WSClient.start() 是阻塞的，会一直保持连接
        ws_client.start()
    except Exception as e:
        logger.error(f"WebSocket 客户端运行异常: {e}")
    finally:
        # 清理事件循环
        try:
            if not loop.is_closed():
                loop.close()
        except Exception:
            pass


class FeishuClientSDK:
    """飞书客户端 - 官方 SDK 实现（支持 WebSocket 长连接模式）"""

    def __init__(
        self,
        app_id: str,
        app_secret: str,
        event_handlers: Optional[Dict[str, Callable[[str], Any]]] = None,
        domain: str = "feishu",
    ):
        """
        初始化飞书客户端

        Args:
            app_id: 飞书应用 ID
            app_secret: 飞书应用密钥
            event_handlers: 事件处理器字典，key 为事件类型，value 为处理函数（接收 JSON 字符串）
            domain: 域名，feishu 或 lark
        """
        if not HAS_SDK:
            raise ImportError(
                "lark_oapi SDK 未安装，请运行: pip install lark_oapi"
            )

        self.app_id = app_id
        self.app_secret = app_secret
        self.event_handlers = event_handlers or {}
        self.domain = domain
        # 解析为完整的 URL
        self._ws_domain = _resolve_domain(domain)

        logger.info(f"飞书 SDK 客户端初始化 (App ID: {app_id}, App Secret: {app_secret[:10]}..., domain: {domain} -> {self._ws_domain})")
        # 验证凭据格式
        if not app_id.startswith("cli_"):
            logger.warning(f"App ID 格式可能不正确，应以 'cli_' 开头: {app_id}")
        if len(app_secret) < 10:
            logger.warning(f"App Secret 长度可能不正确: {app_secret}")

        # 创建 HTTP SDK 客户端（用于发送消息）
        try:
            self.client = Client.builder()\
                .app_id(app_id)\
                .app_secret(app_secret)\
                .build()
            logger.info(f"飞书 SDK HTTP 客户端初始化完成")
        except Exception as e:
            logger.error(f"SDK 客户端初始化失败: {e}")
            raise

        # WebSocket 长连接相关
        self._ws_client: Optional[WSClient] = None
        self._ws_thread: Optional[threading.Thread] = None
        self._ws_started: bool = False

        # HTTP 客户端（用于发送消息）
        self._http_client: httpx.AsyncClient = None
        self._access_token: Optional[str] = None
        self._token_expire_time: float = 0

    def _create_event_dispatcher(self) -> Optional[EventDispatcherHandler]:
        """创建事件分发器"""
        if not self.event_handlers:
            logger.warning("未设置事件处理器，长连接将无法处理消息")
            return None

        # 创建内部事件分发器
        class InternalEventDispatcher:
            def __init__(self, handlers: Dict[str, Callable[[str], Any]]):
                self.handlers = handlers

            def do_without_validation(self, payload: str) -> Optional[Dict[str, Any]]:
                """处理事件（不验证）"""
                try:
                    # payload 可能是 bytes 类型，需要解码为字符串
                    if isinstance(payload, bytes):
                        payload = payload.decode('utf-8', errors='ignore')

                    # 解析 JSON 获取事件类型
                    event_data = json.loads(payload)
                    event_type = event_data.get("header", {}).get("event_type")

                    # 查找对应的处理器
                    handler = self.handlers.get(event_type)
                    if handler:
                        logger.debug(f"收到事件: {event_type}, payload: {payload[:200]}...")
                        result = handler(payload)
                        # 返回成功响应
                        return {"msg": "success"}
                    else:
                        # 静默忽略未注册的事件类型（如 message_read_v1 等）
                        return {"msg": "success"}

                except json.JSONDecodeError as e:
                    logger.error(f"事件 JSON 解析失败: {e}")
                except Exception as e:
                    logger.error(f"事件处理异常: {e}")

                return {"msg": "failed"}

        return InternalEventDispatcher(self.event_handlers)

    def start_ws(self) -> bool:
        """
        启动 WebSocket 长连接

        Returns:
            是否启动成功
        """
        if not HAS_WS_CLIENT:
            logger.error("lark_oapi WebSocket 客户端未安装，无法启动长连接")
            return False

        if self._ws_started:
            logger.warning("WebSocket 长连接已启动")
            return True

        logger.info("启动飞书 WebSocket 长连接...")

        try:
            # 创建事件分发器
            event_dispatcher = self._create_event_dispatcher()
            if not event_dispatcher:
                logger.warning("未设置事件处理器，长连接将无法处理消息")

            # 创建 WebSocket 客户端，使用完整的 domain URL
            logger.debug(f"使用 WebSocket domain URL: {self._ws_domain}")

            self._ws_client = WSClient(
                app_id=self.app_id,
                app_secret=self.app_secret,
                log_level=LogLevel.INFO,
                event_handler=event_dispatcher,
                domain=self._ws_domain,
                auto_reconnect=True,
            )

            # 在新线程中运行 WebSocket 客户端
            # 使用独立函数来确保在新线程中创建新的事件循环
            self._ws_thread = threading.Thread(
                target=_run_ws_in_new_thread,
                args=(self._ws_client,),
                daemon=True,
                name="FeishuWSClient"
            )
            self._ws_thread.start()

            # 等待一下让线程启动
            time.sleep(0.5)

            self._ws_started = True
            logger.info("飞书 WebSocket 长连接已启动（在后台线程中运行）")
            return True

        except Exception as e:
            logger.error(f"启动 WebSocket 长连接失败: {e}")
            return False

    def stop_ws(self) -> None:
        """停止 WebSocket 长连接"""
        logger.info("停止飞书 WebSocket 长连接...")

        self._ws_started = False

        # lark_oapi.ws.Client 没有显式的 stop 方法
        # 通过设置标志位和线程 daemon=True 让线程自然退出（连接断开后）
        self._ws_client = None
        self._ws_thread = None

        logger.info("飞书 WebSocket 长连接已停止")

    async def _get_access_token(self) -> str:
        """获取访问令牌"""
        # 检查缓存是否有效
        if self._access_token and time.time() < self._token_expire_time - 300:
            return self._access_token

        # 获取新令牌
        url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"

        payload = {
            "app_id": self.app_id,
            "app_secret": self.app_secret,
        }

        if not self._http_client:
            self._http_client = httpx.AsyncClient(timeout=30.0)

        logger.debug(f"获取 Token: app_id={self.app_id}, url={url}")

        response = await self._http_client.post(url, json=payload)

        logger.debug(f"Token 响应状态: {response.status_code}")

        response.raise_for_status()

        data = response.json()

        logger.debug(f"Token 响应数据: code={data.get('code')}, msg={data.get('msg')}")

        if data.get("code") != 0:
            logger.error(f"获取 Token 失败详细: code={data.get('code')}, msg={data.get('msg')}, payload={payload}")
            raise Exception(f"获取 Token 失败: {data.get('msg')}")

        access_token = data.get("tenant_access_token")
        expire = data.get("expire", 7200)

        self._access_token = access_token
        self._token_expire_time = time.time() + expire

        logger.debug(f"Token 已刷新，有效期 {expire} 秒")

        return access_token

    async def send_message(
        self,
        receive_id: str,
        message_type: str,
        content: Any,
        receive_id_type: str = "open_id"
    ) -> bool:
        """
        发送消息

        Args:
            receive_id: 接收者 ID
            message_type: 消息类型 (text / interactive / post / card 等)
            content: 消息内容
            receive_id_type: ID 类型

        Returns:
            是否发送成功
        """
        try:
            # 获取访问令牌
            access_token = await self._get_access_token()

            # 内容序列化
            if isinstance(content, (dict, list)):
                content_json = json.dumps(content, ensure_ascii=False)
            else:
                content_json = json.dumps({"text": str(content)}, ensure_ascii=False)

            # 构建请求 - receive_id_type 作为 URL 查询参数
            url = f"https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type={receive_id_type}"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }

            payload = {
                "receive_id": receive_id,
                "msg_type": message_type,
                "content": content_json,
            }

            if not self._http_client:
                self._http_client = httpx.AsyncClient(timeout=30.0)

            response = await self._http_client.post(url, json=payload, headers=headers)
            data = response.json()

            if data.get("code") == 0:
                message_id = data.get("data", {}).get("message_id", "")
                logger.debug(f"消息发送成功: msg_id={message_id}")
                return True
            else:
                logger.debug(f"消息发送失败: code={data.get('code')}, msg={data.get('msg')}")
                return False

        except Exception as e:
            logger.error(f"发送消息异常: {e}")
            return False

    async def send_text_message(
        self,
        receive_id: str,
        text: str,
        receive_id_type: str = "open_id"
    ) -> bool:
        """
        发送文本消息

        Args:
            receive_id: 接收者 ID
            text: 文本内容
            receive_id_type: ID 类型

        Returns:
            是否发送成功
        """
        return await self.send_message(
            receive_id=receive_id,
            message_type="text",
            content={"text": text},
            receive_id_type=receive_id_type,
        )

    async def send_card_message(
        self,
        receive_id: str,
        card: Dict[str, Any],
        receive_id_type: str = "open_id"
    ) -> bool:
        """
        发送卡片消息

        Args:
            receive_id: 接收者 ID
            card: 卡片内容
            receive_id_type: ID 类型

        Returns:
            是否发送成功
        """
        return await self.send_message(
            receive_id=receive_id,
            message_type="interactive",
            content=card,
            receive_id_type=receive_id_type,
        )

    @property
    def is_ws_started(self) -> bool:
        """WebSocket 是否已启动"""
        return self._ws_started

    async def close(self):
        """关闭客户端"""
        logger.info("关闭飞书客户端...")

        # 停止 WebSocket 长连接
        self.stop_ws()

        # 关闭 HTTP 客户端
        if self._http_client:
            await self._http_client.aclose()
            self._http_client = None

        logger.info("飞书客户端已关闭")


# 向后兼容的别名
FeishuClient = FeishuClientSDK


__all__ = ["FeishuClientSDK", "FeishuClient", "HAS_SDK", "HAS_WS_CLIENT"]
