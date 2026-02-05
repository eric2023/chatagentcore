# ChatAgentCore

> 聊天机器人核心项目 - AI 驱动的对话系统基础设施

## 项目愿景

ChatAgentCore 是一个中间服务程序，作为 Qt AI 应用与国内主流聊天软件之间的桥接中间件，支持多平台并发交互，配置驱动，提供统一的通用接口规范。

**核心功能：**
- 支持飞书、企业微信、钉钉三大平台接入（按顺序实现）
- 使用官方 SDK **WebSocket 长连接**方式收发消息，无需公网 IP
- 提供模块化的消息处理和路由组件
- 实现 HTTP API + WebSocket 双接口模式
- 支持动态配置管理
- 可在个人电脑上轻量部署

---

## 快速开始

### 环境要求

| 类别 | 要求 |
|------|------|
| 操作系统 | Linux / macOS / Windows |
| Python | 3.10+ |
| Git | 2.30+ |

### 安装依赖

```bash
# 创建虚拟环境（推荐）
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 方式一：从 pyproject.toml 安装（推荐）
pip install -e .

# 方式二：从 requirements.txt 安装
pip install -r requirements.txt
```

### 配置文件

```bash
# 复制配置文件
cp config/config.yaml.example config/config.yaml

# 编辑配置文件，填入平台凭证
nano config/config.yaml
```

### 启动服务

```bash
# 启动服务
python main.py --config config/config.yaml
```

---

## 目录结构

```
chatagentcore/
├── core/                  # 核心服务层
│   ├── router.py          # 消息路由
│   ├── event_bus.py       # 事件总线
│   ├── config_manager.py  # 配置管理
│   └── adapter_manager.py # 适配器管理
├── adapters/              # 平台适配层
│   ├── base.py            # 适配器基类
│   ├── feishu/            # 飞书适配器（第一阶段）
│   ├── wecom/             # 企业微信适配器（第二阶段）
│   └── dingtalk/          # 钉钉适配器（第三阶段）
├── api/                   # 接口层
│   ├── main.py            # FastAPI 应用入口
│   ├── routes/            # HTTP API 路由
│   ├── websocket/         # WebSocket 管理
│   ├── models/            # 数据模型
│   └── schemas/           # 配置 Schema
├── storage/               # 数据层
│   ├── cache.py           # 消息缓存
│   └── logger.py          # 日志管理
├── cli/                   # 命令行工具
│   └── test_feishu_ws.py  # WebSocket 长连接测试工具
├── config/                # 配置文件
│   └── config.yaml        # 主配置文件
├── tests/                 # 测试
│   ├── unit/              # 单元测试
│   ├── integration/       # 集成测试
│   └── e2e/               # 端到端测试
├── tasks/                 # ⭐ 任务和计划跟踪
├── docs/                  # ⭐ 技术文档
│   ├── architecture/      # 架构设计文档
│   └── sop/               # 开发规范和 SOP
├── CLAUDE.md              # AI 上下文索引
└── README.md              # 本文件
```

---

## 平台接入方式

### 飞书（第一阶段）

| 操作 | 说明 |
|------|------|
| **发送消息** | 使用 App ID + App Secret 调用飞书 API |
| **接收消息** | WebSocket 长连接订阅事件（无公网 IP 要求） |

#### 获取凭证

1. 访问 [飞书开放平台](https://open.feishu.cn/)
2. 创建应用或使用现有应用
3. 获取 `App ID` 和 `App Secret`
4. 配置事件订阅：在应用「事件与回调」页面选择「使用长连接接收事件」
5. 订阅消息事件：添加 `im.message.receive_v1` 和 `im.message.group_at_v1`

#### 配置文件

```yaml
platforms:
  feishu:
    enabled: true
    type: "app"                    # 应用类型：app (企业自建应用) | group (群机器人)
    app_id: "cli_a909cd66f9f8dbde"
    app_secret: "Fd1XCkfmxlKTxzixnsQ9veKok5ujiaIY"
    connection_mode: "websocket"   # 连接模式：websocket (推荐，无需公网IP) | webhook (需要公网IP)
    domain: "feishu"               # 域名：feishu (国内) | lark (海外)
```

### 企业微信（第二阶段）

| 操作 | 说明 |
|------|------|
| **发送消息** | 使用 CorpID + AgentID + Secret 调用企业微信 API |
| **接收消息** | SDK 长连接订阅事件（待实现） |

### 钉钉（第三阶段）

| 操作 | 说明 |
|------|------|
| **发送消息** | 使用 AppKey + AppSecret 调用钉钉 API |
| **接收消息** | SDK 长连接订阅事件（待实现）|

---

## 接口规范

### 统一通用响应格式

```json
{
  "code": 0,
  "message": "success",
  "data": {},
  "timestamp": 1700000000
}
```

### HTTP API 接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/message/send` | POST | 发送消息到聊天平台 |
| `/api/v1/conversation/list` | GET | 获取会话列表 |
| `/config` | GET | 获取配置 |
| `/health` | GET | 健康检查 |
| `/docs` | GET | Swagger API 文档 |

### 发送消息示例

```bash
curl -X POST "http://localhost:8000/api/v1/message/send" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_api_token" \
  -d '{
    "platform": "feishu",
    "to": "ou_xxxxxxxxxxxxx",
    "message_type": "text",
    "content": "Hello World",
    "conversation_type": "user"
  }'
```

### WebSocket 接口

| 端点 | 说明 |
|------|------|
| `/ws/events` | 实时事件推送 |

---

## 配置说明

### 认证配置（可配置，默认固定 Token）

```yaml
auth:
  type: "fixed_token"    # fixed_token | jwt
  token: "your_api_token"  # 固定 Token
```

### 平台配置示例

#### 飞书（WebSocket 长连接模式）

```yaml
platforms:
  feishu:
    enabled: true
    type: "app"
    app_id: "cli_a909cd66f9f8dbde"
    app_secret: "Fd1XCkfmxlKTxzixnsQ9veKok5ujiaIY"
    connection_mode: "websocket"
    domain: "feishu"
```

#### 飞书（Webhook 回调模式）

```yaml
platforms:
  feishu:
    enabled: true
    type: "app"
    app_id: "cli_a909cd66f9f8dbde"
    app_secret: "Fd1XCkfmxlKTxzixnsQ9veKok5ujiaIY"
    connection_mode: "webhook"
    domain: "feishu"
    verification_token: "your_verification_token"  # Webhook 验证令牌
    encrypt_key: "your_encrypt_key"               # 加密密钥（可选）
```

详细配置说明请参考：[config.yaml.example](config/config.yaml.example)

---

## 技术栈

| 组件 | 选型 |
|------|------|
| 编程语言 | Python 3.10+ |
| Web 框架 | FastAPI |
| WebSocket | fastapi.WebSocket |
| 飞书 SDK | lark_oapi (WebSocket 长连接) |
| HTTP 客户端 | httpx |
| 配置管理 | Pydantic + YAML |
| 日志 | loguru |
| 测试 | pytest + pytest-asyncio |

---

## 平台接入计划

| 阶段 | 平台 | 状态 | 接入方式 |
|------|------|------|----------|
| 第一阶段 | 飞书 | ✅ 已完成 | WebSocket 长连接 |
| 第二阶段 | 企业微信 | 待开发 | SDK 长连接订阅事件 |
| 第三阶段 | 钉钉 | 待开发 | SDK 长连接订阅事件 |

---

## 命令行工具

### WebSocket 长连接测试工具

测试飞书 WebSocket 长连接功能是否正常工作：

```bash
python cli/test_feishu_ws.py
```

测试工具将：
1. 验证 lark_oapi WebSocket 客户端已安装
2. 加载 config.yaml 中的飞书配置
3. 启动 WebSocket 长连接
4. 等待接收飞书消息
5. 实时显示消息统计

**交互命令：**
- `status` - 显示消息统计
- `q` / `quit` / `exit` - 退出程序

---

## 开发流程

本项目遵循**六阶段开发工作流**：

```
研究 → 构思 → 计划 → 执行 → 优化 → 评审
```

详细流程请参考：[开发规范智能体](docs/sop/chatagentcore-dev-skill.md)

### 任务跟踪

- 所有确定执行的任务存放在 `tasks/` 文件夹
- 命名格式：`YYYY-MM-DD-{任务摘要}.md`
- 便于回溯跟踪和经验积累

### 文档管理

- 技术文档存放在 `docs/` 文件夹
- 分类：架构 (architecture/)、API (api/)、指南 (guides/)、SOP (sop/)
- 与代码同步更新

---

## 测试

```bash
# 运行所有测试
pytest

# 运行单元测试
pytest tests/unit/

# 运行集成测试
pytest tests/integration/

# 运行端到端测试
pytest tests/e2e/

# 生成测试覆盖率报告
pytest --cov=chatagentcore --cov-report=html
```

---

## 测试策略

| 测试类型 | 目标 | 工具 |
|----------|------|------|
| 单元测试 | 覆盖率 80%+ | pytest |
| 集成测试 | 关键流程验证 | pytest |
| 端到端测试 | 真实对话场景 | pytest + mock |
| 性能测试 | 并发和响应时间 | Locust |

---

## 编码规范

- **代码风格：** 遵循 PEP 8
- **类型检查：** 启用 mypy 强类型检查
- **文档：** 所有公共 API 包含文档字符串
- **提交信息：** 遵循 [Conventional Commits](https://www.conventionalcommits.org/) 规范

---

## 相关资源

- **许可证：** [Apache License 2.0](LICENSE)
- **飞书 SDK 文档：** [https://open.feishu.cn/document/server-docs/server-side-sdk](https://open.feishu.cn/document/server-docs/server-side-sdk)
- **飞书 WebSocket 长连接：** [https://open.feishu.cn/document/server-docs/websocket/event-listen-overview](https://open.feishu.cn/document/server-docs/websocket/event-listen-overview)

---

## 飞书接入详细说明

### WebSocket 长连接模式（推荐）

**优势：** 无需公网 IP，无需配置 Webhook 回调

**实现原理：**
- 使用 `lark_oapi.ws.Client` 建立与服务器的 WebSocket 连接
- SDK 自动处理认证、心跳和重连
- 事件通过 WebSocket 实时推送

**代码示例：**

```python
from chatagentcore.adapters.feishu import FeishuAdapter

# 创建适配器（WebSocket 模式）
adapter = FeishuAdapter({
    "app_id": "cli_a909cd66f9f8dbde",
    "app_secret": "your_secret",
    "connection_mode": "websocket",
    "domain": "feishu"
})

# 初始化（会自动启动 WebSocket 长连接监听）
await adapter.initialize()

# 设置消息处理器
def handle_message(message):
    print(f"收到消息: {message.content['text']}")

adapter.set_message_handler(handle_message)

# 发送消息
await adapter.send_message(
    to="ou_xxxxxxxxxxxxx",
    message_type="text",
    content="Hello!",
    conversation_type="user"
)

# 查询连接状态
if adapter.is_websocket_connected:
    print("WebSocket 已连接")
```

### Webhook 回调模式（备选）

**适用场景：** 已有公网服务器，需要使用 Webhook

**实现原理：**
- 飞书服务器向配置的回调 URL 推送事件
- 应用监听 Webhook 端点

**代码示例：**

```python
from chatagentcore.adapters.feishu import FeishuAdapter

# 创建适配器（Webhook 模式）
adapter = FeishuAdapter({
    "app_id": "cli_a909cd66f9f8dbde",
    "app_secret": "your_secret",
    "connection_mode": "webhook",
    "domain": "feishu"
})

# 初始化（不会启动长连接，等待 Webhook 回调）
await adapter.initialize()

# 处理 Webhook 回调
event_data = {...}  # 从 HTTP 请求接收
result = adapter.handle_webhook(event_data)
```

---

## 变更记录

| 日期 | 变更内容 |
|------|----------|
| 2026-02-05 | ✅ 实现飞书 WebSocket 长连接 |
| 2026-02-05 | ✅ 修复主程序 event loop 冲突问题 |
| 2026-02-05 | ✅ 更新配置 Schema 支持连接模式选择 |
| 2026-02-04 | 确认技术方案：Python + FastAPI，平台接入顺序：飞书→企业微信→钉钉 |
| 2026-02-04 | 初始化项目仓库 |
| 2026-02-04 | 制定开发规范 SOP |

---

## 许可证

Copyright 2025-2026

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

> http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
