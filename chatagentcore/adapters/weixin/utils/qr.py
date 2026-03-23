"""二维码生成与显示工具

提供二维码生成和终端显示功能。
"""

import sys
from typing import Optional


def generate_qrcode(qrcode_url: str) -> str:
    """生成二维码（返回 URL）

    注意：如果未安装 qrcode 库，直接返回 URL。

    Args:
        qrcode_url: 二维码内容 URL

    Returns:
        二维码 URL
    """
    # 如果安装了 qrcode 库，可以生成二维码图片
    try:
        import qrcode
        # 可选：生成二维码图片并保存
        # qr = qrcode.QRCode(version=1, box_size=10, border=5)
        # qr.add_data(qrcode_url)
        # qr.make(fit=True)
        # img = qr.make_image(fill_color="black", back_color="white")
        # img.save("qrcode.png")
        pass
    except ImportError:
        pass

    return qrcode_url


def display_qrcode_terminal(qrcode_url: str) -> None:
    """在终端显示二维码

    优先使用 qrcode-terminal 库，否则显示 URL。

    Args:
        qrcode_url: 二维码内容 URL
    """
    # 方法 1: 使用 qrcode-terminal 库（推荐）
    try:
        import qrcode_terminal
        print("\n请使用微信扫描以下二维码完成登录：")
        print("-" * 50)
        qrcode_terminal.generate(qrcode_url)
        print("-" * 50)
        print()
        return

    except ImportError:
        pass

    # 方法 2: 使用 qrcode 库生成 ASCII 码
    try:
        import qrcode
        qr = qrcode.QRCode(version=1, box_size=1, border=1)
        qr.add_data(qrcode_url)
        qr.make(fit=True)

        # 使用白色背景和黑色方块生成 ASCII 艺术二维码
        print("\n请使用微信扫描以下二维码完成登录：")
        print("-" * 50)
        qr.print_ascii(invert=True)
        print("-" * 50)
        print()
        return

    except ImportError:
        pass

    # 方法 3: 直接显示 URL（回退方案）
    print("\n请使用微信扫描以下二维码完成登录：")
    print("-" * 50)
    print("二维码 URL:")
    print(qrcode_url)
    print("-" * 50)
    print()
    print("提示：如果无法显示二维码，请访问以下链接：")
    print(qrcode_url)
    print()


def display_qrcode_with_qr_code_terminal(qrcode_url: str, small: bool = True) -> None:
    """使用 qrcode-terminal 库显示二维码

    Args:
        qrcode_url: 二维码内容 URL
        small: 是否使用小尺寸
    """
    try:
        import qrcode_terminal
        kwargs = {"small": True} if small else {}
        qrcode_terminal.generate(qrcode_url, **kwargs)
    except ImportError:
        print(f"[无法显示二维码，请访问]: {qrcode_url}")
