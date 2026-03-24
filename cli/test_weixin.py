"""微信适配器测试工具 - 扫码登录

用于测试微信适配器的扫码登录功能。
"""

import asyncio
from pathlib import Path
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from chatagentcore.adapters.weixin import WeixinAdapter
from loguru import logger
logger.remove()
logger.add(sys.stdout, level="DEBUG", format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <level>{message}</level>")


class WeixinTestTool:
    """微信测试工具"""

    def __init__(self):
        """初始化测试工具"""
        # 配置适配器
        config = {
            "account_id": "default",
            "base_url": "https://ilinkai.weixin.qq.com",
            "cdn_base_url": "https://novac2c.cdn.weixin.qq.com/c2c",
            "state_dir": "~/.openclaw-weixin",
        }

        self.adapter = WeixinAdapter(config)
        self._message_count = 0
        self.last_sender_id = None

        # 设置消息处理器
        self.adapter.set_message_handler(self._handle_message)

    async def test_login(self, continue_chat=True):
        """测试扫码登录"""
        print("\n" + "=" * 60)
        print("微信适配器 - 扫码登录测试")
        print("=" * 60 + "\n")

        try:
            result = await self.adapter.login_with_qr(timeout_ms=600000)

            if result["success"]:
                print("\n" + "=" * 60)
                print("✅ 登录成功！")
                print("=" * 60)
                print(f"账号 ID: {result.get('account_id')}")
                print(f"用户 ID: {result.get('user_id')}")
                print(f"Token: {result.get('bot_token')}")
                print("=" * 60 + "\n")

                # 登录成功后进入交互式对话模式
                if continue_chat:
                    print("\n进入交互式对话模式，输入消息回复，Ctrl+C 退出\n")
                    await self.test_interactive_chat()
            else:
                print("\n" + "=" * 60)
                print("❌ 登录失败")
                print("=" * 60)
                print(f"原因: {result.get('message')}")
                print("=" * 60 + "\n")

        except Exception as e:
            print(f"\n❌ 登录异常: {e}\n")

    def _handle_message(self, message):
        """处理接收到的消息"""
        self._message_count += 1

        # 更新最后一个发送者 ID，用于快速回复
        sender_id = message.sender.get("id", "")
        if sender_id:
            self.last_sender_id = sender_id

        print(f"\n📨 收到消息 #{self._message_count}:")
        print(f"   平台: {message.platform}")
        print(f"   消息ID: {message.message_id}")
        print(f"   发送者: {sender_id}")
        print(f"   时间: {message.timestamp}")

        # 处理消息内容
        content = message.content
        if isinstance(content, dict):
            content_type = content.get("type", "")
            content_text = content.get("text", "")
            has_media = content.get("has_media", False)
            print(f"   类型: {content_type}")
            print(f"   内容: {content_text}")
            if has_media:
                print(f"   媒体: 是")
        else:
            print(f"   内容: {content}")
        print()

    async def test_interactive_chat(self):
        """交互式对话模式 - 接收消息并支持回复"""
        print("=" * 60)
        print("交互式对话模式已启动")
        print("=" * 60)
        print("命令格式: to:用户ID 消息内容")
        print("示例: to:wxid_xxxxx 你好")
        print("或者直接输入内容回复最后一条消息的发送者")
        print("按 Ctrl+C 退出")
        print("=" * 60 + "\n")

        # 等待用户输入
        try:
            loop = asyncio.get_running_loop()
            while True:
                try:
                    # 等待用户输入
                    user_input = await loop.run_in_executor(None, input, "> ")
                    user_input = user_input.strip()

                    if not user_input:
                        continue

                    # 解析用户输入
                    if user_input.startswith("to:"):
                        # 格式: to:用户ID 消息内容
                        parts = user_input[3:].split(None, 1)
                        if len(parts) >= 2:
                            to_user_id = parts[0]
                            text = parts[1]
                            try:
                                await self.adapter.send_text_message(to_user_id, text)
                                print(f"✅ 已发送给 {to_user_id}: {text}\n")
                            except Exception as e:
                                print(f"❌ 发送失败: {e}\n")
                        else:
                            print("❌ 格式错误，请使用: to:用户ID 消息内容\n")
                    else:
                        # 简单回复：发送给最后一个发送者
                        if self.last_sender_id:
                            try:
                                await self.adapter.send_text_message(self.last_sender_id, user_input)
                                print(f"✅ 已发送给 {self.last_sender_id}: {user_input}\n")
                            except Exception as e:
                                print(f"❌ 发送失败: {e}\n")
                        else:
                            print("❌ 没有可回复的目标，请先接收消息或使用 to: 格式\n")

                except EOFError:
                    # 输入流关闭，退出
                    break
                except KeyboardInterrupt:
                    break

        except KeyboardInterrupt:
            print("\n\n")

    async def test_long_poll(self, duration_seconds=60):
        """测试长轮询接收消息"""
        print("\n" + "=" * 60)
        print(f"测试接收消息（持续 {duration_seconds} 秒）...")
        print("=" * 60 + "\n")

        # 确保适配器已初始化
        await self.adapter.initialize()

        try:
            # 等待指定的时长
            await asyncio.sleep(duration_seconds)

            print(f"\n测试结束，共收到 {self._message_count} 条消息\n")

        except KeyboardInterrupt:
            print("\n\n测试被用户中断")

        finally:
            # 关闭适配器
            await self.adapter.shutdown()

    async def test_send_message(self, to_user_id: str, text: str):
        """测试发送消息"""
        print("\n" + "=" * 60)
        print("测试发送消息")
        print("=" * 60 + "\n")

        try:
            message_id = await self.adapter.send_text_message(to_user_id, text)
            print(f"✅ 消息发送成功！")
            print(f"   目标: {to_user_id}")
            print(f"   内容: {text}")
            print(f"   消息ID: {message_id}")
            print()

        except Exception as e:
            print(f"❌ 发送消息失败: {e}\n")

    async def cleanup(self):
        """清理资源"""
        print("\n正在清理资源...")
        try:
            await self.adapter.shutdown()
        except Exception as e:
            print(f"清理时出现警告: {e}")
        print("清理完成\n")


async def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="微信适配器测试工具")
    parser.add_argument(
        "command",
        choices=["login", "receive", "send"],
        help="测试命令: login(登录), receive(接收消息), send(发送消息)",
    )
    parser.add_argument("--to", help="发送消息的目标用户ID（send 命令需要）")
    parser.add_argument("--text", help="发送的消息内容（send 命令需要）")
    parser.add_argument("--duration", type=int, default=60, help="接收消息的持续时长（秒），默认60")

    args = parser.parse_args()

    tool = WeixinTestTool()

    try:
        if args.command == "login":
            # 测试登录
            await tool.test_login()

        elif args.command == "receive":
            # 测试接收消息
            await tool.adapter.initialize()
            await tool.test_long_poll(duration_seconds=args.duration)

        elif args.command == "send":
            # 测试发送消息
            if not args.to or not args.text:
                print("错误: send 命令需要 --to 和 --text 参数")
                return

            await tool.adapter.initialize()
            await tool.test_send_message(args.to, args.text)

    except KeyboardInterrupt:
        print("\n\n测试被用户中断")

    finally:
        await tool.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
