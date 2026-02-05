"""ChatAgentCore 服务入口"""

import argparse
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent))


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="ChatAgentCore - 聊天机器人中间服务")
    parser.add_argument(
        "--host", default="0.0.0.0", help="监听地址"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="监听端口"
    )
    parser.add_argument(
        "--config", default="config/config.yaml", help="配置文件路径"
    )
    parser.add_argument(
        "--debug", action="store_true", help="启用调试模式"
    )
    parser.add_argument(
        "--reload", action="store_true", help="启用自动重载"
    )

    args = parser.parse_args()

    # 导入应用
    from chatagentcore.api.main import app
    from chatagentcore.core.config_manager import get_config_manager
    import uvicorn

    # 加载配置
    config_manager = get_config_manager()
    config_manager.config_path = Path(args.config)
    config_manager.load()

    # 启动服务
    uvicorn.run(
        app,
        host=args.host,
        port=args.port,
        reload=args.reload or args.debug,
        log_level="debug" if args.debug else "info",
    )


if __name__ == "__main__":
    main()
