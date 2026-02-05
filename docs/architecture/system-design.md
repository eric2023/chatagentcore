# ChatAgentCore 系统架构设计

> ChatAgentCore 中间服务系统架构设计文档（基于 SDK 长连接方式）

---

## 目录

- [1. 项目背景与目标](#1-项目背景与目标)
- [2. 技术栈选择](#2-技术栈选择)
- [3. 系统架构](#3-系统架构)
- [4. 核心模块设计](#4-核心模块设计)
- [5. 接口设计](#5-接口设计)
- [6. 消息流程](#6-消息流程)
- [7. 部署方案](#7-部署方案)
- [8. 安全设计](#8-安全设计)
- [9. 扩展性设计](#9-扩展性设计)

---

## 1. 项目背景与目标

### 1.1 背景说明

- **现有资产**: Qt 开发的 AI 应用，具备问答和 Skill 调用能力
- **目标**: 开发一个中间服务程序，适配国内主流聊天软件（飞书、企业微信、钉钉）
- **定位**: 作为 Qt 应用与聊天平台之间的桥接中间件
- **部署环境**: 个人电脑，轻量可靠方案
- **关键变更**: 已迁移至官方 SDK 长连接方式，不再需要公网 IP

### 1.2 核心目标

| 目标 | 描述 |
|------|------|
| 多平台适配 | 支持飞书、企业微信、钉钉三大平台（按顺序接入） |
| 并发交互 | 同时与多个配置的聊天平台保持连接和交互 |
| 配置驱动 | 根据配置文件动态启动和管理多个平台接入服务 |
| 标准接口 | 为 Qt 应用提供通用的统一调用接口 |
| 跨平台部署 | 在个人电脑上直接运行，无需公网 IP（SDK 长连接方式） |

### 1.3 平台接入顺序

| 阶段 | 平台 | 状态 | 接入方式 |
|------|------|------|----------|
| 第一阶段 | 飞书 | ✅ 已完成 | 官方 SDK 长连接 (SSE) |
| 第二阶段 | 企业微信 | 待开发 | SDK 长连接订阅事件 |
| 第三阶段 | 钉钉 | 待开发 | SDK 长连接订阅事件 |

### 1.4 非功能性需求

| 维度 | 要求 |
|------|------|
| **性能** | 单机支持 1000+ concurrent 消息处理 |
| **可靠性** | 消息处理失败自动重试，保证至少一次送达 |
| **可扩展性** | 插件化平台适配器，易于新增平台 |
| **易用性** | 提供命令行 Demo 演示接口调用 |
| **可观测性** | 日志记录完整，支持监控指标 |
| **部署** | 无需公网 IP，SDK 长连接方式可在内网直接运行 |

---

## 2. 技术栈选择

### 2.1 编程语言：Python 3.10+

| 优势 | 说明 |
|------|------|
| **成熟 SDK** | 三大平台都有官方或成熟的 Python SDK |
| **异步支持** | asyncio 原生支持，适合多平台并发处理 |
| **跨平台** | Windows/Linux/macOS 完全支持 |
| **部署轻量** | venv/docker/packaged executable 多种部署方式 |
| **开发效率** | 生态丰富，快速集成各类工具 |
| **团队熟悉度** | Qt Python 绑定经验可复用 |

### 2.2 核心技术组件

| 组件 | 选型 | 说明 |
|------|------|------|
| **Web 框架** | FastAPI | 高性能异步框架，自动 API 文档 |
| **WebSocket** | fastapi.WebSocket | 实时双向通信 |
| **配置管理** | Pydantic + YAML | 类型安全的配置管理 |
| **日志** | loguru | 结构化日志，彩色输出 |
| **测试** | pytest + pytest-asyncio | 异步测试支持 |
| **打包** | PyInstaller | 单文件可执行程序 |
| **依赖管理** | Hatchling | 现代化依赖管理 |
| **飞书 SDK** | lark_oapi + httpx | 官方 SDK，SSE 长连接 |

### 2.3 技术栈决策理由

```
决策路径：
├─ 语言栈：Python
│  ├─ SDK 支持（✅ 三大平台都有成熟 SDK）
│  ├─ 异步能力（✅ asyncio 原生支持）
│  ├─ 跨平台（✅ 全平台支持）
│  ├─ 部署轻量（✅ pip/venv/docker/exe）
│  └─ 开发效率（✅ 生态丰富）
│
├─ Web 框架：FastAPI
│  ├─ 性能（✅ Starlette 异步引擎）
│  ├─ 文档化（✅ 自动 Swagger UI）
│  ├─ 类型安全（✅ Pydantic 模型验证）
│  └─ WebSocket（✅ 原生支持）
│
├─ WebSocket：fastapi.WebSocket
│  ├─ 实时通信（✅ 双向、低延迟）
│  ├─ 简单易用（✅ 与 FastAPI 无缝集成）
│  └─ 连接管理（✅ 支持 Connection Manager）
│
├─ 长连接方案：SDK SSE 方式
│  ├─ 部署简便（✅ 无需公网 IP）
│  ├─ 实时性高（✅ Server-Sent Events）
│  └─ 官方支持（✅ 平台 SDK 内置）
│
└─ 配置管理：Pydantic + YAML
   ├─ 类型安全（✅ 编译时验证）
   ├─ 可维护性（✅ 人性化 YAML 格式）
   └─ 热加载（✅ 支持配置热更新）
```

---

## 3. 系统架构

### 3.1 整体架构图（SDK 长连接方式）

```
                    ┌────────────────────────────────────────────────────────┐
                    │                      聊天平台层                         │
                    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
                    │  │     飞书     │  │   企业微信   │  │     钉钉     │  │
                    │  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘  │
                    └─────────┼─────────────────┼─────────────────┼──────────┘
                              │                 │                 │
                              │  SDK 长连接   │  SDK 长连接   │  SDK 长连接
                              │  (SSE)        │  (订阅)       │  (订阅)
                              │                 │                 │
                              └─────────────────┼─────────────────┘
                                                │
                    ┌───────────────────────────▼────────────────────────────┐
                    │                    接口层                               │
                    │  ┌──────────────────────┐  ┌──────────────────────┐    │
                    │  │  HTTP API Server     │  │  WebSocket Server    │    │
                    │  │  (FastAPI)           │  │  (FastAPI WebSocket)  │    │
                    │  └──────────┬───────────┘  └──────────┬───────────┘    │
                    └─────────────┼───────────────────────────┼──────────────┘
                                  │                           │
                    ┌─────────────┼───────────────────────────┼──────────────┐
                    │             │      核心服务层          │              │
                    │  ┌──────────▼──────────┐  ┌────────────▼─────────────┐ │
                    │  │  Message Router     │  │     Event Bus           │ │
                    │  │  (消息路由)         │  │    (事件总线)           │ │
                    │  └──────────┬──────────┘  └────────────┬─────────────┘ │
                    │             │                           │               │
                    │  ┌──────────▼──────────┐  ┌────────────▼─────────────┐ │
                    │  │  Config Manager     │  │   Adapter Manager       │ │
                    │  │  (配置管理)         │  │   (适配器管理)          │ │
                    │  └─────────────────────┘  └────────────┬─────────────┘ │
                    │                                         │               │
                    └─────────────────────────────────────────┼───────────────┘
                                                              │
                    ┌─────────────────────────────────────────▼───────────────┐
                    │                    平台适配层                             │
                    │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
                    │  │  飞书适配器  │  │企业微信适配器│  │  钉钉适配器  │  │
                    │  │ (SDK长连接)  │  │  (SDK连接)   │  │  (SDK连接)   │  │
                    │  └──────────────┘  └──────────────┘  └──────────────┘  │
                    └───────────────────────────────────────────────────────────┘
                    │
                    │  HTTP POST / WebSocket
                    │
    ┌───────────────▼──────────────────────┐
    │            Qt AI 应用                 │
    │  ──────────────────────────          │
    │  • 问答能力引擎                      │
    │  • Skill 调用能力                    │
    │    调用中间服务接口                  │
    └──────────────────────────────────────┘
```

### 3.2 分层说明

| 层级 | 职责 | 组件 |
|------|------|------|
| **接口层** | 对外提供服务入口 | HTTP API、WebSocket |
| **核心服务层** | 业务逻辑协调 | 消息路由、事件总线、配置管理、适配器管理 |
| **平台适配层** | 平台协议适配（SDK 长连接方式） | 飞书/企业微信/钉钉适配器 |
| **数据层** | 数据持久化和缓存 | 内存缓存、日志存储 |

### 3.3 关键变化：从 Webhook 到 SDK 长连接

| 方面 | 旧方案（Webhook） | 新方案（SDK 长连接） |
|------|-------------------|--------------------|
| **部署要求** | 需公网 IP | 无需公网 IP |
| **网络穿透** | 需要 Cloudflare Tunnel/frp | 不需要 |
| **消息接收** | 被动等待平台推送 | 主动订阅事件流 |
| **连接管理** | 处理 Webhook 请求 | SDK 自动管理连接 |
| **错误恢复** | 依赖超时重试 | SDK 内置重连机制 |

---

## 4. 核心模块设计

### 4.1 目录结构

```
chatagentcore/
├── core/                      # 核心服务层
│   ├── __init__.py
│   ├── router.py              # 消息路由
│   ├── event_bus.py           # 事件总线
│   ├── config_manager.py      # 配置管理
│   └── adapter_manager.py     # 适配器管理
│
├── adapters/                  # 平台适配层
│   ├── __init__.py
│   ├── base.py                # 适配器基类
│   └── feishu/                # 飞书适配器（第一阶段）
│       ├── __init__.py
│       ├── client.py          # SDK 长连接客户端
│       └── models.py          # 数据模型
│
├── api/                       # 接口层
│   ├── __init__.py
│   ├── main.py                # FastAPI 应用入口
│   ├── routes/
│   │   ├── __init__.py
│   │   └── message.py         # 消息接口
│   ├── websocket/
│   │   ├── __init__.py
│   │   └── manager.py         # WebSocket 管理
│   ├── models/
│   │   ├── __init__.py
│   │   └── message.py         # 消息模型
│   └── schemas/
│       ├── __init__.py
│       └── config.py          # 配置 Schema
│
├── storage/                   # 数据层
│   ├── __init__.py
│   └── logger.py              # 日志管理
│
├── cli/                       # 命令行工具
│   ├── __init__.py
│   ├── demo.py                # 接口调用示例
│   ├── verify_feishu_sdk.py   # SDK 验证脚本
│   └── feishu_interactive.py  # 交互式测试工具
│
├── config/                    # 配置文件
│   └── config.yaml            # 主配置文件
│
├── tests/                     # 测试
│   ├── conftest.py
│   └── unit/
│
├── pyproject.toml             # 项目配置
├── main.py                    # 服务入口
└── README.md                  # 项目说明
```

### 4.2 核心模块详解

#### 4.2.1 适配器基类

```python
# 核心职责：
# 1. 定义平台适配器的统一接口
# 2. send_message：发送消息到平台
# 3. set_message_handler：设置消息处理器（长连接方式）

class BaseAdapter(ABC):
    @abstractmethod
    async def send_message(
        self, to: str, message_type: str, content: str, conversation_type: str = "user"
    ) -> str:
        """发送消息到平台

        Args:
            to: 接收者 ID（用户 ID 或群 ID）
            message_type: 消息类型 text | image | card
            content: 消息内容
            conversation_type: 会话类型 user | group

        Returns:
            发送后的消息 ID
        """
        pass

    def set_message_handler(self, handler):
        """设置消息处理器（长连接方式）

        Args:
            handler: 消息处理函数
        """
        pass

    async def initialize(self) -> None:
        """初始化适配器，启动长连接监听"""
        pass

    async def shutdown(self) -> None:
        """关闭适配器，停止长连接"""
        pass
```

#### 4.2.2 飞书适配器（SDK 长连接）

```python
# 使用飞书官方 SDK 建立 SSE 长连接
class FeishuAdapter(BaseAdapter):
    def __init__(self, config: Dict):
        self.app_id = config["app_id"]
        self.app_secret = config["app_secret"]
        self._client = FeishuClientSDK(
            app_id=self.app_id,
            app_secret=self.app_secret,
            event_handlers={"message": self._handle_message}
        )
        self._message_handler = None

    def set_message_handler(self, handler):
        self._message_handler = handler
        self._client.set_event_handler("message", handler)

    async def initialize(self):
        """启动飞书 SDK 长连接"""
        self._client.start_event_listener()

    async def send_message(self, to, message_type, content, conversation_type="user"):
        """通过 SDK 发送消息"""
        return await self._client.send_text_message(to, content)
```

#### 4.2.3 配置管理

```yaml
# config.yaml - SDK 长连接方式配置
platforms:
  feishu:
    enabled: true
    type: "app"
    config:
      app_id: "cli_xxx"
      app_secret: "xxx"
  # 注意：长连接方式无需配置 webhook_base_url、verification_token 等
```

---

## 5. 接口设计

### 5.1 接口方式选择

| 接口类型 | 方式 | 用途 |
|----------|------|------|
| **Qt → 中间服务** | HTTP POST | 同步调用（发送指令、查询状态） |
| **中间服务 → Qt** | WebSocket | 异步推送（接收用户消息、通知事件） |
| **聊天平台 → 中间服务** | SDK 长连接 (SSE) | 官方 SDK 订阅事件 |

### 5.2 统一通用接口规范

所有接口遵循统一的通用规范：

| 字段 | 类型 | 说明 |
|------|------|------|
| `code` | int | 状态码：0-成功，非0-失败 |
| `message` | str | 响应消息描述 |
| `data` | object | 响应数据 |
| `timestamp` | int | 响应时间戳（Unix 时间） |

#### 5.2.1 发送消息到聊天平台

```http
POST /api/v1/message/send
Content-Type: application/json
Authorization: Bearer {token}

{
  "platform": "feishu",        # 平台: feishu | wecom | dingtalk
  "to": "user_id",             # 接收者：用户ID/群ID
  "message_type": "text",      # 消息类型: text | image | card
  "content": "Hello World",    # 消息内容
  "conversation_type": "user"  # 会话类型: user | group
}

Response:
{
  "code": 0,
  "message": "success",
  "data": {
    "message_id": "msg_123",
    "status": "sent"
  },
  "timestamp": 1700000000
}
```

#### 5.2.2 查询消息状态

```http
POST /api/v1/message/status
Content-Type: application/json
Authorization: Bearer {token}

{
  "platform": "feishu",
  "message_id": "msg_123"
}

Response:
{
  "code": 0,
  "message": "success",
  "data": {
    "message_id": "msg_123",
    "status": "sent",           # sent | delivered | read | failed
    "sent_at": "2026-02-04T15:30:00Z"
  },
  "timestamp": 1700000000
}
```

#### 5.2.3 管理平台配置

```http
# 获取配置
GET /api/v1/config
Authorization: Bearer {token}

# 更新配置
POST /api/v1/config
Content-Type: application/json
Authorization: Bearer {token}

{
  "platform": "feishu",
  "enabled": true
}

Response:
{
  "code": 0,
  "message": "success",
  "data": {
    "platform": "feishu",
    "status": "active"
  },
  "timestamp": 1700000000
}
```

### 5.3 WebSocket 接口设计

#### 5.3.1 连接与认证

```javascript
// 客户端连接
const ws = new WebSocket('ws://localhost:8000/ws/events');

// 认证（首次消息需携带 Token）
ws.send(JSON.stringify({
  type: 'auth',
  token: 'your_token'
}));
```

#### 5.3.2 接收消息

```javascript
ws.onmessage = (event) => {
  const data = JSON.parse(event.data);

  switch(data.type) {
    case 'message':
      // 新消息
      console.log('New message:', data.payload);
      break;
    case 'event':
      // 事件通知
      console.log('Event:', data.payload);
      break;
    case 'error':
      // 错误通知
      console.error('Error:', data.payload);
      break;
  }
};
```

---

## 6. 消息流程

### 6.1 标准消息流程（SDK 长连接方式）

```
用户发消息
    │
    ▼
┌───────────────┐          SDK 长连接 (SSE)
│  聊天平台     │ ──────────────────────────────►
└───────────────┘
    │                                          │
    │  发送消息                                │
    │                                          │
    │          ┌───────────────────────────────▼───────────────┐
    │          │         ChatAgentCore SDK 长连接接收            │
    │          └───────────────────────────────┬───────────────┘
    │                                          │
    │                                   原始消息
    │                                          │
    │          ┌───────────────────────────────▼───────────────┐
    │          │               消息路由 (Router)               │
    │          │     解析平台消息 → 统一格式转换                │
    │          └───────────────────────────────┬───────────────┘
    │                                          │
    │                                  统一消息格式
    │                                          │
    │          ┌───────────────────────────────▼───────────────┐
    │          │              事件总线 (EventBus)              │
    │          │     发布消息事件 → 分发给订阅者                │
    │          └───────────────────────────────┬───────────────┘
    │                                          │
    │        ┌─────────────────────────────────┼─────────────────┐
    │        │                                 │                 │
    │   ┌────▼─────┐                     ┌────▼─────┐           │
    │   │WebSocket │                     │  日志    │           │
    │   │ 推送到   │                     │  记录    │           │
    │   │ 客户端   │                     └──────────┘           │
    │   └────┬─────┘                                             │
    │        │                                                   │
    │   推送消息                                                 │
    │        │                                                   │
    │        ▼                                                   │
    │   ┌───────────────┐                                        │
    │   │   Qt AI 应用  │                                        │
    │   │  ────────────│                                        │
    │   │  接收用户消息 │                                        │
    │   │  处理 + Skill│                                        │
    │   │     调用     │                                        │
    │   └──────┬───────┘                                        │
    │          │                                                   │
    │    生成回复                                                 │
    │          │                                                   │
    │          │ HTTP POST 调用接口                               │
    │          │                                                   │
    │          ▼                                                   │
    │   ┌────────────────────┐                                    │
    │   │ ChatAgentCore API  │                                    │
    │   │   接收发送请求      │                                    │
    │   └────────┬───────────┘                                    │
    │            │                                               │
    │            │ 路由到对应适配器                               │
    │            ▼                                               │
    │   ┌────────────────────┐                                    │
    │   │  消息路由 (Router) │                                    │
    │   └────────┬───────────┘                                    │
    │            │                                               │
    │            │ 统一格式 → 平台格式                            │
    │            ▼                                               │
    │   ┌────────────────────┐                                    │
    │   │   平台适配器       │                                    │
    │   │  (Platform Adapter)│                                    │
    │   └────────┬───────────┘                                    │
    │            │                                               │
    │            │ 调用平台 API                                   │
    │            ▼                                               │
    │   ┌────────────────────┐                                    │
    │   │   平台 API         │                                    │
    │   └────────┬───────────┘                                    │
    │            │                                               │
    │            │ 发送回复到平台                                 │
    │            ▼                                               │
    │   ┌────────────────────┐                                    │
    │   │   聊天平台         │                                    │
    │   └────────┬───────────┘                                    │
    │            │                                               │
    │            │ 用户收到回复                                   │
    │            ▼                                               │
    │   ┌────────────────────┐                                    │
    │   │      用户          │                                    │
    │   └────────────────────┘                                    │
    │                                                            │
    └────────────────────────────────────────────────────────────┘
```

### 6.2 数据流向（长连接方式）

| 步骤 | 方向 | 说明 |
|------|------|------|
| 1 | 平台 → 服务 | SDK 长连接推送用户消息 (SSE) |
| 2 | 服务 → Qt | WebSocket 推送消息事件 |
| 3 | Qt → 服务 | HTTP POST 发送回复 |
| 4 | 服务 → 平台 | API 调用发送消息 |

---

## 7. 部署方案

### 7.1 部署形态

```
个人电脑部署（无需公网 IP）
      │
      ├─ 方案 A：虚拟环境（推荐）
      │   ├─ python -m venv venv
      │   ├─ venv/Scripts/pip install -e .
      │   └─ venv/Scripts/python main.py --config config/config.yaml
      │
      ├─ 方案 B：可执行文件
      │   └─ ChatAgentCore.exe --config config/config.yaml
      │
      └─ 方案 C：Docker（仅开发/测试）
          └─ docker run --env-file .env chatagentcore
```

### 7.2 配置文件结构

```yaml
# config.yaml - SDK 长连接方式
server:
  host: "0.0.0.0"
  port: 8000
  # 注意：长连接方式无需配置 webhook_base_url
  debug: false

# 认证配置（可配置，默认固定 Token）
auth:
  type: "fixed_token"    # fixed_token | jwt
  token: "your_api_token"  # 固定 Token（当 type=fixed_token 时使用）
  # jwt 配置（当 type=jwt 时使用）
  jwt_secret: "your_jwt_secret"
  jwt_algorithm: "HS256"
  jwt_expire_hours: 24

# 平台配置（简化版 - SDK 长连接方式）
platforms:
  # 第一阶段：飞书（已完成）
  feishu:
    enabled: true
    type: "app"  # app | group
    config:
      app_id: "cli_xxx"
      app_secret: "xxx"
      # 注意：无需配置 verification_token、encrypt_key

  # 第二阶段：企业微信（待实现）
  wecom:
    enabled: false
    type: "app"
    config:
      corp_id: "ww123456789"
      agent_id: "1000002"
      secret: "your_secret"

  # 第三阶段：钉钉（待实现）
  dingtalk:
    enabled: false
    type: "app"
    config:
      app_key: "your_app_key"
      app_secret: "your_app_secret"

# 日志配置
logging:
  level: "INFO"
  file: "logs/chatagentcore.log"
  rotation: "10 MB"
  retention: "30 days"
```

### 7.3 安装依赖

```bash
# 安装项目依赖
pip install -e .

# 飞书 SDK必需
pip install lark_oapi httpx
```

### 7.4 运行命令

```bash
# 启动服务
python main.py --config config/config.yaml

# 带调试模式启动
python main.py --config config/config.yaml --debug

# 后台运行 (Linux)
nohup python main.py --config config/config.yaml > logs/server.log 2>&1 &
```

---

## 8. 安全设计

### 8.1 认证与授权（可配置）

| 组件 | 方式 | 说明 |
|------|------|------|
| **API 接口** | 可配置 Token 认证 | 默认固定 Token，可选 JWT |
| **WebSocket** | 握手认证 | 首次消息携带 Token |
| **SDK 长连接** | Token 认证 | 各平台官方 SDK 内置处理 |
| **平台 API** | OAuth2 / API Key | 各平台官方认证 |

### 8.2 数据加密

| 数据类型 | 加密方式 |
|----------|----------|
| SDK 长连接消息 | AES-256 (平台官方/SDK 自动处理) |
| API 通信 | TLS 1.3 |
| 配置文件 | 明文（本地环境） |

### 8.3 安全建议

- Token 定期轮换
- 配置文件避免提交到 Git
- 生产环境启用 HTTPS
- 限制访问 IP（可选）

---

## 9. 扩展性设计

### 9.1 新增平台步骤

```
1. 在 adapters/ 下创建新平台目录
2. 继承 BaseAdapter 抽象类
3. 实现使用官方 SDK 的长连接客户端
4. 在 config.yaml 添加平台配置
5. 在 AdapterManager 注册新适配器
```

### 9.2 插件化架构

```python
# adapters/base.py
from abc import ABC, abstractmethod

class BaseAdapter(ABC):
    @abstractmethod
    async def send_message(self, to: str, message_type: str, content: str, conversation_type: str = "user") -> str:
        """发送消息"""
        pass

    def set_message_handler(self, handler):
        """设置消息处理器（长连接方式）"""
        pass
```

---

**文档版本:** 3.0.0
**最后更新:** 2026-02-04
**状态:** 已确认，已实现 SDK 长连接方式
**相关文档:**
- [平台接入调研](./platform-research.md)
- [开发规范智能体](../sop/chatagentcore-dev-skill.md)
- [飞书官方文档](https://open.feishu.cn/document)
- [企业微信官方文档](https://developer.work.weixin.qq.com)
- [钉钉官方文档](https://open.dingtalk.com)
