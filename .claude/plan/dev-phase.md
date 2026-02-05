# ChatAgentCore 开发阶段计划

## 任务上下文

| 项目 | 内容 |
|------|------|
| 技术栈 | Python 3.10+, FastAPI, Pydantic, loguru |
| 平台接入 | 飞书（第一阶段）- SDK 长连接方式 |
| 接口方式 | HTTP POST + WebSocket |
| 认证方式 | 可配置（默认固定 Token） |
| 关键变更 | 迁移至 SDK 长连接方式，无需公网 IP |

## 方案：渐进式迭代开发（SDK 长连接模式）

---

## 阶段 1：基础框架

| 步骤 | 操作 | 原子操作 | 预期结果 |
|------|------|---------|----------|
| 1.1 | 创建目录结构 | - 创建 core/, adapters/, api/, storage/, cli/, config/, tests/ 目录及子目录 | 目录结构完整 |
| 1.2 | 初始化依赖管理 | - 创建 pyproject.toml（定义项目元数据、依赖包括 lark_oapi） | 可安装依赖 |
| 1.3 | 配置开发工具 | - 创建 .editorconfig, .gitignore, .env.example | 开发环境就绪 |
| 1.4 | 配置基础日志 | - 创建 storage/logger.py（loguru 配置） | 日志模块可用 |
| 1.5 | 配置 Schema 定义 | - 创建 api/schemas/config.py（Pydantic 设置模型，简化配置） | 配置模型验证可用 |

## 阶段 2：核心服务层

| 步骤 | 操作 | 原子操作 | 预期结果 |
|------|------|---------|----------|
| 2.1 | 适配器基类 | - 创建 adapters/base.py（抽象基类，定义 send_message，set_message_handler） | 适配器契约定义 |
| 2.2 | 事件总线 | - 创建 core/event_bus.py（发布订阅机制，支持 channel 订阅） | 事件分发可用 |
| 2.3 | 配置管理器 | - 创建 core/config_manager.py（YAML 加载，热重载） | 配置动态管理可用 |
| 2.4 | 适配器管理器 | - 创建 core/adapter_manager.py（动态加载/卸载/重载适配器） | 适配器生命周期管理 |
| 2.5 | 消息路由 | - 创建 core/router.py（路由到适配器，格式转换） | 消息路由可用 |

## 阶段 3：接口层

| 步骤 | 操作 | 原子操作 | 预期结果 |
|------|------|---------|----------|
| 3.1 | 数据模型 | - 创建 api/models/message.py（统一消息格式） | 消息模型定义 |
| 3.2 | WebSocket 管理器 | - 创建 api/websocket/manager.py（连接管理，消息推送） | WebSocket 连接管理 |
| 3.3 | API 路由 | - 创建 api/routes/message.py（send, status, conversation, config） | HTTP API 端点 |
| 3.4 | FastAPI 应用 | - 创建 api/main.py（初始化 app，注册路由，中间件） | 服务可启动 |
| 3.5 | 入口文件 | - 创建 main.py（服务启动入口） | 命令行可启动 |

## 阶段 4：飞书适配器（SDK 长连接）

| 步骤 | 操作 | 原子操作 | 预期结果 |
|------|------|---------|----------|
| 4.1 | 飞书数据模型 | - 创建 adapters/feishu/models.py（消息、事件模型） | 飞书协议模型 |
| 4.2 | 飞书 SDK 长连接客户端 | - 创建 adapters/feishu/client.py（官方SDK，SSE长连接订阅事件） | 长连接监听可用 |
| 4.3 | 飞书适配器实现 | - 创建 adapters/feishu/__init__.py（继承 BaseAdapter，集成SDK） | 飞书适配器完整 |

## 阶段 5：Demo 与测试

| 步骤 | 操作 | 原子操作 | 预期结果 |
|------|------|---------|----------|
| 5.1 | 配置示例 | - 创建 config/config.yaml.example（简化版配置，无需webhook配置） | 用户可参考配置 |
| 5.2 | 命令行 Demo | - 创建 cli/demo.py（send, status 命令示例） | 接口调用演示 |
| 5.3 | SDK 验证脚本 | - 创建 cli/verify_feishu_sdk.py（Token验证、连接测试） | SDK 连接验证 |
| 5.4 | 交互式测试工具 | - 创建 cli/feishu_interactive.py（长连接监听+交互式回复） | 交互式测试 |
| 5.5 | 单元测试框架 | - 创建 tests/conftest.py（pytest fixture） | 测试框架就绪 |
| 5.6 | 核心模块测试 | - 创建 tests/unit/test_event_bus.py, test_config_manager.py | 核心模块覆盖 |

## 关键依赖

```toml
[dependencies]
fastapi = "^0.109"
uvicorn = {extras = ["standard"], version = "^0.27"}
pydantic = "^2.5"
pydantic-settings = "^2.1"
loguru = "^0.7"
pyyaml = "^6.0"
python-multipart = "^0.0.6"
httpx = "^0.25"
cryptography = "^41.0"
lark-oapi = "^1.2.0"  # 飞书官方 SDK（长连接）

[dev-dependencies]
pytest = "^7.4"
pytest-asyncio = "^0.23"
pytest-cov = "^4.1"
black = "^23.12"
ruff = "^0.1"
mypy = "^1.8"
```

## 目录结构（SDK 长连接方式）

```
chatagentcore/
├── .claude/
│   └── plan/
│       └── dev-phase.md
├── core/
│   ├── __init__.py
│   ├── router.py
│   ├── event_bus.py
│   ├── config_manager.py
│   └── adapter_manager.py
├── adapters/
│   ├── __init__.py
│   ├── base.py
│   └── feishu/
│       ├── __init__.py
│       ├── client.py          # SDK 长连接客户端
│       └── models.py
├── api/
│   ├── __init__.py
│   ├── main.py
│   ├── routes/
│   │   ├── __init__.py
│   │   └── message.py
│   ├── websocket/
│   │   ├── __init__.py
│   │   └── manager.py
│   ├── models/
│   │   ├── __init__.py
│   │   └── message.py
│   └── schemas/
│       ├── __init__.py
│       └── config.py
├── storage/
│   ├── __init__.py
│   ├── cache.py
│   └── logger.py
├── cli/
│   ├── __init__.py
│   ├── demo.py
│   ├── verify_feishu_sdk.py   # SDK 验证
│   └── feishu_interactive.py  # 交互式测试
├── config/
│   └── config.yaml.example
├── tests/
│   ├── conftest.py
│   └── unit/
├── pyproject.toml
├── main.py
└── .editorconfig
```

## 计划状态

- **创建日期**: 2026-02-04
- **版本**: 2.0.0 (SDK 长连接版)
- **阶段**: 计划完成
- **总步骤数**: 20
