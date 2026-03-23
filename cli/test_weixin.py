"""微信适配器测试工具 - 扫码登录

用于测试微信适配器的扫码登录功能。
"""

import asyncio
import sys
import os

# 添加项目根目录到路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

from chatagentcore.adapters.weixin import WeixinAdapter
from loguru import logger


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

        # 设置消息处理器
        self.adapter.set_message_handler(self._handle_message)

    async def test_login(self):
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
        print(f"\n📨 收到消息 #{self._message_count}:")
        print(f"   平台: {message.platform}")
        print(f"   消息ID: {message.message_id}")
        print(f"   发送者: {message.sender['id']}")
        print(f"   时间: {message.timestamp}")
        print(f"   内容: {message.content}")
        print()

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
        await self.adapter.shutdown()
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
