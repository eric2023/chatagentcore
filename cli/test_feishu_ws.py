#!/usr/bin/env python3
"""飞书 WebSocket 双向对话测试工具

支持接收飞书消息并通过命令行回复，实现双向对话功能。
"""

import asyncio
import json
import sys
import threading
import time
from pathlib import Path
from typing import Dict, Any, Optional, Callable
from loguru import logger
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from chatagentcore.core.config_manager import get_config_manager
from chatagentcore.adapters.feishu.client import FeishuClientSDK, HAS_WS_CLIENT


class ChatSession:
    """会话状态管理"""

    def __init__(self):
        self.client: Optional[FeishuClientSDK] = None
        self.target_open_id: Optional[str] = None
        self.target_chat_id: Optional[str] = None
        self.last_sender_id: Optional[str] = None
        self.last_chat_id: Optional[str] = None
        self.message_count = 0
        self.running = True
        self.pending_messages: list = []
        self.send_loop: Optional[asyncio.AbstractEventLoop] = None
        self.send_queue: list = []  # 待发送消息队列

    def set_reply_target(self, sender_id: str, chat_id: str, chat_type: str) -> None:
        """设置回复目标"""
        self.last_sender_id = sender_id
        self.last_chat_id = chat_id
        # 根据会话类型设置目标
        if chat_type == "group":
            self.target_chat_id = chat_id
        else:
            self.target_open_id = sender_id

    def get_reply_target(self) -> tuple[Optional[str], str, str]:
        """获取回复目标 (id, id_type, conversation_type)"""
        if self.target_open_id:
            return self.target_open_id, "open_id", "user"
        elif self.target_chat_id:
            return self.target_chat_id, "chat_id", "group"
        elif self.last_sender_id:
            return self.last_sender_id, "open_id", "user"
        else:
            raise ValueError("没有可回复的目标，请先发一条消息来建立会话")

    def add_message(self, message_info: dict) -> None:
        """添加收到的消息"""
        self.message_count += 1
        self.pending_messages.append(message_info)

    def has_new_messages(self) -> bool:
        """是否有新消息"""
        return len(self.pending_messages) > 0

    def get_new_messages(self) -> list:
        """获取并清空新消息"""
        messages = self.pending_messages.copy()
        self.pending_messages.clear()
        return messages


# 全局会话实例
CHAT_SESSION = ChatSession()


def print_welcome_banner() -> None:
    """打印欢迎界面"""
    banner = """
╔════════════════════════════════════════════════════════════╗
║            飞书 WebSocket 双向对话工具                     ║
║       ChatAgentCore - Feishu Interactive Chat               ║
╚════════════════════════════════════════════════════════════╝

使用说明:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
1. 向机器人发送消息建立会话
2. 命令行直接输入文本回复消息
3. 命令:
   /status      - 查看连接状态和消息统计
   /set 目标ID  - 设置回复目标 ID
   /clear       - 清屏
   /help        - 显示帮助
   /quit /exit  - 退出程序
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
    print(banner)


def print_message_received(message_info: dict):
    """打印接收到的消息"""
    # 安全处理时间戳 - 使用整数除法避免超大整数问题
    timestamp_ms = message_info.get("timestamp", 0)
    try:
        # 尝试转换为秒级时间戳
        timestamp_s = timestamp_ms // 1000 if timestamp_ms > 10000000000 else timestamp_ms
        timestamp = datetime.fromtimestamp(timestamp_s)
    except Exception:
        timestamp = datetime.now()

    sender_name = message_info.get("sender_name", "用户")
    content = message_info.get("content", "")

    print(f"\n[{timestamp.strftime('%H:%M:%S')}] 📨 {sender_name}:")
    print("-" * 60)
    print(content)
    print("-" * 60)
    print(f"\n回复: ", end="", flush=True)


def create_event_handler() -> Callable[[str], Dict[str, Any]]:
    """创建消息事件处理器"""

    def handle_message(payload: str) -> Dict[str, Any]:
        """接收并处理飞书消息"""
        try:
            # payload 可能是 bytes 类型
            if isinstance(payload, bytes):
                payload = payload.decode('utf-8', errors='ignore')

            event_data = json.loads(payload)
            header = event_data.get("header", {})
            event = event_data.get("event", {})

            # 飞书事件结构: event.message.message_id / chat_id / message_type / content
            message_obj = event.get("message", {})
            if not message_obj:
                # 尝试从 data 获取
                data = event.get("data", {})
                if data:
                    message_obj = data.get("message", {})

            # 如果还是没有，使用 event 本身
            if not message_obj:
                message_obj = event

            # 提取消息信息
            sender_id = ""
            chat_id = message_obj.get("chat_id", "")
            chat_type = message_obj.get("chat_type") or ("group" if chat_id and chat_id.startswith("oc_") else "user")

            # 解析发送者 ID - 事件可能在不同位置
            sender_info = event.get("sender")
            if not sender_info:
                # 尝试从 data 获取
                data = event.get("data", {})
                sender_info = data.get("sender")

            if sender_info:
                if "sender_id" in sender_info:
                    sender_id_obj = sender_info.get("sender_id", {})
                    sender_id = sender_id_obj.get("open_id", "")
                elif "open_id" in sender_info:
                    sender_id = sender_info["open_id"]
                elif "user_id" in sender_info:
                    sender_id = sender_info["user_id"]

            # 解析消息类型和内容
            message_type = message_obj.get("message_type") or message_obj.get("msg_type", "")
            content_raw = message_obj.get("content", "")
            text_content = ""

            if isinstance(content_raw, str):
                try:
                    content_obj = json.loads(content_raw)
                    if isinstance(content_obj, dict):
                        text_content = content_obj.get("text", "")
                except json.JSONDecodeError:
                    text_content = content_raw
            elif isinstance(content_raw, dict):
                text_content = content_raw.get("text", "")

            # 更新会话状态
            if sender_id and chat_id:
                CHAT_SESSION.set_reply_target(sender_id, chat_id, chat_type)
                logger.info(f"会话状态已更新: sender_id={sender_id}, chat_id={chat_id}, chat_type={chat_type}")
            else:
                logger.warning(f"无法建立会话: sender_id={sender_id}, chat_id={chat_id}")
                logger.debug(f"事件数据: {json.dumps(event_data, ensure_ascii=False)[:500]}")

            # 保存消息供显示
            # 安全处理时间戳 - 避免超大整数浮点运算
            create_time = message_obj.get("create_time") or header.get("create_time", 0)
            timestamp_ms = 0
            try:
                # create_time 可能是秒级时间戳，需要转为毫秒
                if create_time and isinstance(create_time, int):
                    timestamp_ms = create_time * 1000
            except Exception:
                timestamp_ms = 0

            message_info = {
                "timestamp": timestamp_ms,
                "sender_id": sender_id,
                "chat_id": chat_id,
                "chat_type": chat_type,
                "sender_name": "用户" if chat_type == "user" else "群成员",
                "content": text_content,
                "msg_type": message_type,
            }

            CHAT_SESSION.add_message(message_info)

            # 在主线程打印消息
            print_message_received(message_info)

            return {"msg": "success"}

        except Exception as e:
            logger.error(f"消息处理异常: {e}")
            return {"msg": "failed"}

    return handle_message


def run_ws_client(session: ChatSession):
    """在后台线程中运行 WebSocket 客户端"""
    try:
        event_handlers = {
            "im.message.receive_v1": create_event_handler(),
            "im.message.group_at_v1": create_event_handler(),
        }

        session.client = FeishuClientSDK(
            app_id=session.app_id,
            app_secret=session.app_secret,
            event_handlers=event_handlers,
            domain=session.domain,
        )

        session.client.start_ws()

    except Exception as e:
        logger.error(f"WebSocket 客户端异常: {e}")
        session.running = False


def _run_async_in_loop(coro) -> Any:
    """在共享的事件循环中运行异步任务"""
    if CHAT_SESSION.send_loop is None or CHAT_SESSION.send_loop.is_closed():
        # 创建新的事件循环
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        CHAT_SESSION.send_loop = loop

    # 在现有事件循环中运行任务
    try:
        future = asyncio.run_coroutine_threadsafe(coro, CHAT_SESSION.send_loop)
        return future.result(timeout=30)
    except Exception as e:
        logger.error(f"运行异步任务失败: {e}")
        raise


async def send_reply(text: str) -> bool:
    """发送回复消息"""
    try:
        target_id, id_type, conv_type = CHAT_SESSION.get_reply_target()

        logger.info(f"发送消息到: {target_id} ({conv_type})")
        logger.info(f"内容: {text}")

        if conv_type == "user":
            result = await CHAT_SESSION.client.send_text_message(
                receive_id=target_id,
                text=text,
                receive_id_type=id_type
            )
        else:  # group
            result = await CHAT_SESSION.client.send_text_message(
                receive_id=target_id,
                text=text,
                receive_id_type=id_type
            )

        if result:
            print(f"✅ 发送成功 ({datetime.now().strftime('%H:%M:%S')})")
        else:
            print("❌ 发送失败")

        return result

    except Exception as e:
        logger.error(f"发送失败: {e}")
        print(f"❌ 发送失败: {e}")
        return False


def show_status():
    """显示状态"""
    print("\n" + "=" * 60)
    print("📊 状态信息")
    print("-" * 60)
    print(f"连接状态: {'✅ 已连接' if CHAT_SESSION.client and CHAT_SESSION.client.is_ws_started else '❌ 未连接'}")
    print(f"接收消息数: {CHAT_SESSION.message_count}")

    if CHAT_SESSION.last_sender_id:
        print(f"最后发送者: {CHAT_SESSION.last_sender_id}")
    if CHAT_SESSION.last_chat_id:
        print(f"最后会话: {CHAT_SESSION.last_chat_id}")
    if CHAT_SESSION.target_open_id:
        print(f"回复目标(用户): {CHAT_SESSION.target_open_id}")
    if CHAT_SESSION.target_chat_id:
        print(f"回复目标(群): {CHAT_SESSION.target_chat_id}")

    print("=" * 60)


def show_help():
    """显示帮助"""
    print("\n" + "=" * 60)
    print("📖 命令帮助")
    print("-" * 60)
    print("直接输入文本 → 回复消息")
    print("/status      → 查看连接状态")
    print("/set <ID>    → 设置回复目标 ID")
    print("/clear       → 清屏")
    print("/help        → 显示帮助")
    print("/quit /exit  → 退出程序")
    print("=" * 60)


def main():
    """主函数"""
    print_welcome_banner()

    # 验证 SDK
    if not HAS_WS_CLIENT:
        logger.error("❌ lark_oapi WebSocket 客户端未安装")
        logger.info("请运行: pip install lark_oapi websockets")
        sys.exit(1)

    logger.info("✅ lark_oapi WebSocket 客户端已安装")

    # 初始化用于发送消息的事件循环
    send_loop = asyncio.new_event_loop()
    asyncio.set_event_loop(send_loop)
    CHAT_SESSION.send_loop = send_loop

    # 启动事件循环线程
    def run_event_loop():
        asyncio.set_event_loop(send_loop)
        asyncio.run(send_loop.run_forever())

    loop_thread = threading.Thread(target=run_event_loop, daemon=True)
    loop_thread.start()

    # 加载配置
    config_manager = get_config_manager()
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"

    if not config_path.exists():
        logger.error(f"配置文件不存在: {config_path}")
        logger.info("请复制 config/config.yaml.example 为 config/config.yaml 并填写配置")
        sys.exit(1)

    config_manager.config_path = config_path
    config_manager.load()

    feishu_config = config_manager.config.platforms.feishu

    if not feishu_config.enabled:
        logger.error("❌ 飞书平台未启用")
        sys.exit(1)

    # 设置会话凭证
    CHAT_SESSION.app_id = feishu_config.app_id
    CHAT_SESSION.app_secret = feishu_config.app_secret
    CHAT_SESSION.domain = getattr(feishu_config, "domain", "feishu") or "feishu"

    logger.info(f"App ID: {CHAT_SESSION.app_id}")

    # 启动 WebSocket 客户端（后台线程）
    ws_thread = threading.Thread(target=run_ws_client, args=(CHAT_SESSION,), daemon=True)
    ws_thread.start()

    # 等待连接建立
    time.sleep(2)

    print("\n✅ WebSocket 连接已启动")
    print("\n💡 请向机器人发第一条消息建立会话，然后即可开始对话")
    print("输入 /help 查看命令\n")

    # 主循环：等待用户输入
    while CHAT_SESSION.running:
        try:
            user_input = input().strip()

            if not user_input:
                continue

            # 处理命令
            if user_input.lower() in ("q", "quit", "exit"):
                print("\n👋 再见！")
                CHAT_SESSION.running = False
                break

            elif user_input.lower() == "/help":
                show_help()
                print("回复: ", end="", flush=True)

            elif user_input.lower() == "/status":
                show_status()
                print("\n回复: ", end="", flush=True)

            elif user_input.lower() == "/clear":
                import os
                os.system("clear" if os.name != "nt" else "cls")
                print_welcome_banner()
                print("\n回复: ", end="", flush=True)

            elif user_input.lower().startswith("/set "):
                parts = user_input.split(" ", 1)
                if len(parts) > 1:
                    CHAT_SESSION.target_open_id = parts[1].strip()
                    print(f"✅ 已设置回复目标: {parts[1]}")
                else:
                    print("❌ 用法: /set 目标ID")
                print("\n回复: ", end="", flush=True)

            else:
                # 发送消息 - 使用同步包装函数避免事件循环关闭问题
                _run_async_in_loop(send_reply(user_input))
                print("\n回复: ", end="", flush=True)

        except (EOFError, KeyboardInterrupt):
            print("\n\n👋 再见！")
            CHAT_SESSION.running = False
            break

    # 清理
    logger.info("程序退出")


if __name__ == "__main__":
    main()
