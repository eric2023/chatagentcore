# ChatAgentCore

> 聊天机器人核心项目 - AI 驱动的对话系统基础设施

## 项目简介

ChatAgentCore 是一个中间服务程序，作为 Qt AI 应用与国内主流聊天软件之间的桥接中间件，支持多平台并发交互，配置驱动，提供统一的通用接口规范。

**核心功能：**
- 支持飞书、企业微信、钉钉三大平台接入
- 使用官方 SDK **WebSocket 长连接**方式收发消息，无需公网 IP
- 提供模块化的消息处理和路由组件
- 实现 HTTP API 接口
- 支持动态配置管理
- 可在个人电脑上轻量部署

---

## 快速开始

### 环境要求

| 类别 | 要求 |
|------|------|
| 操作系统 | Linux / macOS / Windows |
| Python | 3.10+ |

### 安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
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
# 启动主程序
python -c "
import sys
sys.path.insert(0, '.')
from chatagentcore.api.main import app
import uvicorn
uvicorn.run(app, host='0.0.0.0', port=8000)
"
```

### 测试工具

```bash
# 启动交互式飞书测试工具
python cli/test_feishu_ws.py
```

---

## 飞书接入详细说明

### 创建飞书应用

1. 访问 [飞书开放平台](https://open.feishu.cn)
2. 创建 **企业自建应用**
3. 在 **凭证与基础信息** 页面获取 `App ID` 和 `App Secret`

### 必需权限

| 权限 | 范围 | 说明 |
|------|------|------|
| `im:message` | 消息 | 发送和接收消息 |
| `im:message.p2p_msg:readonly` | 私聊 | 读取发给机器人的私聊消息 |
| `im:message.group_at_msg:readonly` | 群聊 | 接收群内 @机器人的消息 |
| `im:message:send_as_bot` | 发送 | 以机器人身份发送消息 |
| `im:resource` | 媒体 | 上传和下载图片/文件 |

### 事件订阅 ⚠️

> **这是最容易遗漏的配置！** 如果机器人能发消息但收不到消息，请检查此项。

在飞书开放平台的应用后台，进入 **事件与回调** 页面：

1. **事件订阅方式**：选择 **使用长连接接收事件**（推荐，无需公网 IP）
2. **添加事件订阅**，勾选以下事件：

   | 事件 | 说明 |
   |------|------|
   | `im.message.receive_v1` | 接收消息（必需） |
   | `im.message.message_read_v1` | 消息已读回执（可选） |
   | `im.chat.member.bot.added_v1` | 机器人进群（可选） |
   | `im.chat.member.bot.deleted_v1` | 机器人被移出群（可选） |

3. 确保事件订阅的权限已申请并通过审核

### 配置文件示例

```yaml
platforms:
  feishu:
    enabled: true                    # 是否启用
    type: "app"                       # 应用类型：app (企业自建应用) | group (群机器人)
    app_id: "cli_a909cd66f9f8dbde"    # 飞书应用 ID
    app_secret: "your_app_secret"     # 飞书应用密钥
    connection_mode: "websocket"      # 连接模式：websocket (推荐，无需公网IP) | webhook
    domain: "feishu"                  # 域名：feishu (国内) | lark (海外)
```

### 连接模式说明

#### WebSocket 长连接模式（推荐）

**优势：** 无需公网 IP，无需配置 Webhook 回调地址

**实现原理：**
- 使用 `lark_oapi.ws.Client` 建立与服务器的 WebSocket 连接
- SDK 自动处理认证、心跳和重连
- 事件通过 WebSocket 实时推送

#### Webhook 回调模式（备选）

**适用场景：** 已有公网服务器，需要使用 Webhook

**实现原理：**
- 飞书服务器向配置的回调 URL 推送事件
- 应用监听 Webhook 端点

---

## 常见问题

### 机器人能发消息但收不到消息

检查以下配置：
1. 是否配置了 **事件订阅**？（见上方事件订阅章节）
2. 事件订阅方式是否选择了 **长连接**？
3. 是否添加了 `im.message.receive_v1` 事件？
4. 相关权限是否已申请并审核通过？

### 返回消息时 403 错误

确保已申请 `im:message:send_as_bot` 权限，并且权限已审核通过。

### 在飞书里找不到机器人

1. 确保应用已发布（至少发布到测试版本）
2. 在飞书搜索框中搜索机器人名称
3. 检查应用可用范围是否包含你的账号

---

## HTTP API 接口

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

---

## 技术栈

| 组件 | 选型 |
|------|------|
| 编程语言 | Python 3.10+ |
| Web 框架 | FastAPI |
| 飞书 SDK | lark_oapi (WebSocket 长连接) |
| HTTP 客户端 | httpx |
| 配置管理 | Pydantic + YAML |
| 日志 | loguru |

---

## 目录结构

```
chatagentcore/
├── core/                  # 核心服务层
├── adapters/              # 平台适配层
│   ├── feishu/            # 飞书适配器
│   ├── wecom/             # 企业微信适配器（待开发）
│   └── dingtalk/          # 钉钉适配器（待开发）
├── api/                   # 接口层
├── cli/                   # 命令行工具
├── config/                # 配置文件
├── docs/                  # 技术文档
└── tasks/                 # 任务和计划跟踪
```

---

## 变更记录

| 日期 | 变更内容 |
|------|----------|
| 2026-02-05 | ✅ 实现飞书 WebSocket 长连接及双向对话 |

---

## 许可证

Apache License 2.0
