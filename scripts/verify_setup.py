#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""环境验证脚本 - 验证 ChatAgentCore 运行环境是否就绪

检查项：
- Python 版本 >= 3.10
- 必需依赖是否安装
- 配置文件是否存在
- 目录结构是否完整
"""

import sys
import os
from pathlib import Path


def check_python_version():
    """检查 Python 版本"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 10:
        return True, f"Python {version.major}.{version.minor}.{version.micro} ✅"
    else:
        return False, f"Python {version.major}.{version.minor}.{version.micro} ❌ (需要 >= 3.10)"


def check_dependencies():
    """检查必需依赖"""
    required = [
        "fastapi",
        "uvicorn",
        "pydantic",
        "pyyaml",
        "loguru",
        "httpx",
        "lark_oapi",
        "pycryptodome",
        "websockets",
    ]

    results = []
    all_ok = True

    for module in required:
        try:
            __import__(module)
            results.append((True, f"{module} ✅"))
        except ImportError:
            results.append((False, f"{module} ❌ 未安装"))
            all_ok = False

    return all_ok, results


def check_config_file():
    """检查配置文件"""
    config_path = Path("config/config.yaml")
    if config_path.exists():
        return True, f"配置文件存在: {config_path} ✅"
    else:
        example_path = Path("config/config.yaml.example")
        if example_path.exists():
            return False, f"配置文件不存在 ❌ (但存在示例: {example_path})"
        return False, f"配置文件不存在: {config_path} ❌"


def check_directory_structure():
    """检查目录结构"""
    required_dirs = [
        "chatagentcore/core",
        "chatagentcore/adapters",
        "chatagentcore/api",
        "chatagentcore/cli",
        "config",
        "tests",
    ]

    results = []
    all_ok = True

    for dir_path in required_dirs:
        path = Path(dir_path)
        if path.exists():
            results.append((True, f"{dir_path} ✅"))
        else:
            results.append((False, f"{dir_path} ❌ 不存在"))
            all_ok = False

    return all_ok, results


def check_cli_scripts():
    """检查 CLI 测试脚本"""
    required_scripts = [
        "cli/test_feishu_ws.py",
        "cli/test_weixin.py",
    ]

    results = []
    all_ok = True

    for script in required_scripts:
        path = Path(script)
        if path.exists():
            results.append((True, f"{script} ✅"))
        else:
            results.append((False, f"{script} ❌ 不存在"))
            all_ok = False

    return all_ok, results


def main():
    """主函数"""
    print("=" * 70)
    print("ChatAgentCore 环境验证")
    print("=" * 70)

    all_checks_pass = True

    # 检查 Python 版本
    print("\n[1/5] Python 版本检查")
    python_ok, python_msg = check_python_version()
    print(f"  {python_msg}")
    if not python_ok:
        all_checks_pass = False

    # 检查依赖
    print("\n[2/5] 依赖包检查")
    deps_ok, deps_results = check_dependencies()
    for ok, msg in deps_results:
        print(f"  {msg}")
    if not deps_ok:
        print(f"  💡 安装命令: pip install -r requirements.txt")
        all_checks_pass = False

    # 检查配置文件
    print("\n[3/5] 配置文件检查")
    config_ok, config_msg = check_config_file()
    print(f"  {config_msg}")
    if not config_ok:
        print(f"  💡 复制命令: cp config/config.yaml.example config/config.yaml")
        all_checks_pass = False

    # 检查目录结构
    print("\n[4/5] 目录结构检查")
    dirs_ok, dirs_results = check_directory_structure()
    for ok, msg in dirs_results:
        print(f"  {msg}")
    if not dirs_ok:
        all_checks_pass = False

    # 检查 CLI 脚本
    print("\n[5/5] CLI 测试脚本检查")
    cli_ok, cli_results = check_cli_scripts()
    for ok, msg in cli_results:
        print(f"  {msg}")
    if not cli_ok:
        all_checks_pass = False

    # 总结
    print("\n" + "=" * 70)
    if all_checks_pass:
        print("✅ 环境验证通过！可以开始使用 ChatAgentCore")
        print("\n快速开始：")
        print("  1. 配置文件: 编辑 config/config.yaml")
        print("  2. 启动服务: python main.py")
        print("  3. 测试工具: python cli/test_feishu_ws.py")
    else:
        print("❌ 环境验证失败！请按照上述提示修复问题")
    print("=" * 70)

    return 0 if all_checks_pass else 1


if __name__ == "__main__":
    sys.exit(main())
