"""ChatAgentCore 服务入口"""

import argparse
import sys
import uvicorn
from pathlib import Path
from loguru import logger

# 确保项目根目录在 Python 路径中
# 如果是打包环境，使用可执行文件所在目录；如果是源码环境，使用 main.py 所在目录
if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent.absolute()
else:
    BASE_DIR = Path(__file__).parent.absolute()

sys.path.insert(0, str(BASE_DIR))


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="ChatAgentCore - 聊天机器人中间服务")
    parser.add_argument(
        "--host", help="监听地址 (覆盖配置文件)"
    )
    parser.add_argument(
        "--port", type=int, help="监听端口 (覆盖配置文件)"
    )
    parser.add_argument(
        "--config", default="config/config.yaml", help="配置文件路径"
    )
    parser.add_argument(
        "--debug", action="store_true", help="启用调试模式"
    )
    parser.add_argument(
        "--reload", action="store_true", help="启用自动重载 (开发模式)"
    )

    args = parser.parse_args()

    # 延迟导入，确保 sys.path 已更新
    from chatagentcore.api.main import app
    from chatagentcore.core.config_manager import get_config_manager

    # 加载配置
    config_manager = get_config_manager(args.config)
    try:
        config_manager.load()
    except Exception as e:
        print(f"加载配置文件失败: {e}")
        sys.exit(1)

    # 确定最终运行参数
    host = args.host if args.host else config_manager.config.server.host
    port = args.port if args.port else config_manager.config.server.port
    reload_mode = args.reload or args.debug or config_manager.config.server.debug
    log_level = "debug" if (args.debug or config_manager.config.server.debug) else "info"

    logger.info(f"正在启动 ChatAgentCore...")
    logger.info(f"监听地址: {host}:{port}")
    logger.info(f"配置文件: {args.config}")

    # 启动服务
    uvicorn.run(
        "chatagentcore.api.main:app",
        host=host,
        port=port,
        reload=reload_mode,
        log_level=log_level,
    )


if __name__ == "__main__":
    main()
