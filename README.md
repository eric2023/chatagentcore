# ChatAgentCore

> 聊天机器人核心项目 - AI 驱动的对话系统基础设施

## 项目简介

ChatAgentCore 是一个中间服务程序，作为 Qt AI 应用与国内主流聊天软件之间的桥接中间件，支持多平台并发交互，配置驱动，提供统一的通用接口规范。

**核心功能：**
- ✅ 飞书：支持 WebSocket 长连接方式收发消息
- ✅ 微信：支持 HTTP JSON API 长轮询方式接入，完整对话能力
- 🔧 钉钉：适配器待完善
- 🔧 企业微信：适配器待开发
- 提供模块化的消息处理和路由组件
- 实现 HTTP API 接口
- 支持动态配置管理
- 可在个人电脑上轻量部署

---

## 快速体验（5 分钟上手）

### 1. 环境检查

```bash
python scripts/verify_setup.py
```

预期输出：
```
✅ 环境验证通过！可以开始使用 ChatAgentCore
```

### 2. 安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置复制

```bash
# 复制配置文件
cp config/config.yaml.example config/config.yaml

# 编辑配置文件
nano config/config.yaml
```

**必填配置**：
- `auth.token`: 设置你的 API Token
- `platforms.feishu.app_secret`: 替换为实际的飞书应用密钥
- 如需使用微信，设置 `platforms.weixin.enabled: true`

### 4. 启动服务

```bash
# 方式 1：直接启动
python main.py

# 方式 2：开发模式（自动重载）
python main.py --reload

# 方式 3：指定端口
python main.py --port 8080
```

启动成功输出：
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 5. 发送测试消息

```bash
# 飞书测试（需要先配置 App Secret）
python cli/test_feishu_ws.py

# 微信测试（需要先扫码登录）
python cli/test_weixin.py login
```

---

## 服务管理

### 启动服务

**方式 1：直接运行**
```bash
python main.py
```

**方式 2：指定参数**
```bash
python main.py --host 0.0.0.0 --port 8000
```

**方式 3：开发模式**
```bash
python main.py --reload  # 代码变动自动重启
```

**方式 4：调试模式**
```bash
python main.py --debug
```

### 停止服务

按 `Ctrl + C` 停止服务

### 重启服务

```bash
# 停止后重新启动
python main.py
```

### 日志查看

```bash
# 查看最新日志
tail -f logs/chatagentcore.log

# 查看错误日志
grep ERROR logs/chatagentcore.log
```

### 健康检查

```bash
# 检查服务状态
curl http://localhost:8000/health

# 预期输出
# {"status":"healthy","plugins_loaded":1}
```

---

## 平台配置

### 飞书配置

#### 创建飞书应用

1. 访问 [飞书开放平台](https://open.feishu.cn)
2. 创建 **企业自建应用**
3. 在 **凭证与基础信息** 页面获取 `App ID` 和 `App Secret`

#### 必需权限

| 权限 | 范围 | 说明 |
|------|------|------|
| `im:message` | 消息 | 发送和接收消息 |
| `im:message.p2p_msg:readonly` | 私聊 | 读取发给机器人的私聊消息 |
| `im:message.group_at_msg:readonly` | 群聊 | 接收群内 @机器人的消息 |
| `im:message:send_as_bot` | 发送 | 以机器人身份发送消息 |
| `im:resource` | 媒体 | 上传和下载图片/文件 |

#### 事件订阅 ⚠️

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

#### 配置文件示例

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

---

### 微信配置

微信适配器支持通过扫码方式登录，无需申请应用。

#### 扫码登录

```bash
# 使用测试工具扫码登录
python cli/test_weixin.py login
```

登录成功后，Token 会自动保存到 `~/.openclaw-weixin/accounts/{account_id}.json`

#### 配置示例

```yaml
platforms:
  weixin:
    enabled: true                    # 是否启用
    account_id: "default"            # 账号标识
    base_url: "https://ilinkai.weixin.qq.com"  # API 基础 URL
    cdn_base_url: "https://novac2c.cdn.weixin.qq.com/c2c"  # CDN 基础 URL
    state_dir: "~/.openclaw-weixin"   # 状态目录（Token 自动保存位置）
    token: ""                        # Bot Token（可选，扫码登录后自动保存）
```

详细文档请参考：[微信适配器文档](docs/adapters/weixin.md)

---

### 钉钉配置（待完善）

```yaml
platforms:
  dingtalk:
    enabled: false
    type: "app"
    app_key: "your_app_key"         # 从钉钉开放平台获取
    app_secret: "your_app_secret"   # 从钉钉开放平台获取
    connection_mode: "websocket"     # 连接模式：websocket | webhook
```

---

### QQ 机器人配置

```yaml
platforms:
  qq:
    enabled: false
    type: "app"
    app_id: "your_app_id"           # 从 QQ 机器人后台获取 (AppID)
    token: "your_token"             # 从 QQ 机器人后台获取 (Token/AppSecret)
```

---

## 测试指南

### 独立测试（CLI 工具）

#### 飞书测试

启动交互式飞书测试工具：

```bash
python cli/test_feishu_ws.py
```

**使用说明**：
- 在飞书中向机器人发送消息建立会话
- 命令行输入文本即可回复
- 支持命令：`/status`、`/set 目标ID`、`/clear`、`/help`、`/quit`

#### 微信测试

**1. 扫码登录**
```bash
python cli/test_weixin.py login
```

**2. 接收消息**
```bash
# 默认 60 秒
python cli/test_weixin.py receive

# 指定时长 120 秒
python cli/test_weixin.py receive --duration 120
```

**3. 发送消息**
```bash
python cli/test_weixin.py send --to "xxx@im.wechat" --text "你好，世界！"
```

---

### 集成测试（HTTP API）

#### 配置 Token

在 `config/config.yaml` 中设置：

```yaml
auth:
  token: "your_api_token_here"
```

#### 发送消息示例

```bash
curl -X POST "http://localhost:8000/api/v1/message/send" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_api_token_here" \
  -d '{
    "platform": "feishu",
    "to": "ou_xxxxxxxxxxxxx",
    "message_type": "text",
    "content": "Hello World",
    "conversation_type": "user"
  }'
```

**响应示例**：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "message_id": "msg_id_xxxxx",
    "status": "sent"
  },
  "timestamp": 1711234567
}
```

#### 查询消息状态

```bash
curl -X POST "http://localhost:8000/api/v1/message/status" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_api_token_here" \
  -d '{
    "platform": "feishu",
    "message_id": "msg_id_xxxxx"
  }'
```

#### 获取会话列表

```bash
curl -X POST "http://localhost:8000/api/v1/conversation/list" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your_api_token_here" \
  -d '{
    "platform": "feishu"
  }'
```

---

## API 参考

### 认证方式

**Bearer Token 认证**

所有 API 请求需要在 Header 中携带 Token：

```http
Authorization: Bearer your_api_token_here
```

Token 在 `config/config.yaml` 的 `auth.token` 中配置。

---

### 接口清单

| 接口 | 方法 | 说明 |
|------|------|------|
| `/api/v1/message/send` | POST | 发送消息到聊天平台 |
| `/api/v1/message/status` | POST | 查询消息状态 |
| `/api/v1/conversation/list` | POST | 获取会话列表 |
| `/api/config` | GET | 获取配置 |
| `/config` | GET | 获取配置（旧接口） |
| `/health` | GET | 健康检查 |
| `/docs` | GET | Swagger API 文档 |
| `/redoc` | GET | ReDoc API 文档 |
| `/admin` | GET | 管理后台界面 |

---

### 发送消息

**接口**：`POST /api/v1/message/send`

**请求参数**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| platform | string | 是 | 平台名称：feishu / weixin / dingtalk / qq |
| to | string | 是 | 接收者 ID |
| message_type | string | 是 | 消息类型：text / image / card |
| content | string/object | 是 | 消息内容 |
| conversation_type | string | 否 | 会话类型：user / group，默认 user |

**请求示例**：
```json
{
  "platform": "feishu",
  "to": "ou_xxxxxxxxxxxxx",
  "message_type": "text",
  "content": "你好，这是测试消息",
  "conversation_type": "user"
}
```

**响应示例**：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "message_id": "msg_id_xxxxx",
    "status": "sent"
  },
  "timestamp": 1711234567
}
```

---

### 查询消息状态

**接口**：`POST /api/v1/message/status`

**请求参数**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| platform | string | 是 | 平台名称 |
| message_id | string | 是 | 消息 ID |

**请求示例**：
```json
{
  "platform": "feishu",
  "message_id": "msg_id_xxxxx"
}
```

**响应示例**：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "platform": "feishu",
    "message_id": "msg_id_xxxxx",
    "status": "sent",
    "sent_at": 1711234567
  },
  "timestamp": 1711234567
}
```

---

### 获取会话列表

**接口**：`POST /api/v1/conversation/list`

**请求参数**：

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| platform | string | 是 | 平台名称 |
| cursor | string | 否 | 分页游标 |
| limit | number | 否 | 每页数量，默认 20 |

**响应示例**：
```json
{
  "code": 0,
  "message": "success",
  "data": {
    "conversations": [
      {
        "conversation_id": "oc_xxxxxxx",
        "conversation_type": "user",
        "unread_count": 2
      }
    ],
    "has_more": false,
    "cursor": null
  },
  "timestamp": 1711234567
}
```

---

## 故障排查

### 服务启动失败

**问题**：启动时提示模块找不到

**解决方案**：
```bash
# 检查依赖安装
pip install -r requirements.txt

# 检查 Python 版本
python --version  # 需要 >= 3.10
```

---

### Token 无效

**问题**：返回 403 错误 "Invalid token"

**解决方案**：
1. 检查 `config/config.yaml` 中的 `auth.token`
2. 确保请求 Header 中携带正确的 Token
3. Token 格式：`Authorization: Bearer your_token`

---

### 机器人收不到消息

**飞书**：
1. 检查是否配置了 **事件订阅**
2. 确认事件订阅方式选择了 **长连接**
3. 验证 `im.message.receive_v1` 事件已添加
4. 检查相关权限是否已审核通过

**微信**：
1. 确认已扫码登录成功
2. 检查 `state_dir` 目录下是否有 Token 文件
3. 确认长轮询状态正常

---

### 在飞书里找不到机器人

1. 确保应用已发布（至少发布到测试版本）
2. 在飞书搜索框中搜索机器人名称
3. 检查应用可用范围是否包含你的账号

---

### 日志位置

默认日志文件：`logs/chatagentcore.log

```bash
# 实时查看日志
tail -f logs/chatagentcore.log

# 查看错误
grep ERROR logs/chatagentcore.log

# 查看特定平台日志
grep "飞书" logs/chatagentcore.log
```

---

### WebSocket 连接断开

**现象**：连接频繁断开或无法建立

**排查**：
1. 检查网络连接
2. 确认应用凭证（App Secret）正确
3. 查看服务日志中的错误信息

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
│   ├── base.py            # 适配器基类
│   ├── feishu/            # ✅ 飞书适配器
│   ├── weixin/            # ✅ 微信适配器
│   ├── dingtalk/          # 🔧 钉钉适配器（待完善）
│   └── qq/                # 🔧 QQ 适配器
├── api/                   # 接口层
├── cli/                   # 命令行工具
│   ├── test_feishu_ws.py  # 飞书测试工具
│   ├── test_qq_ws.py      # QQ 测试工具
│   └── test_weixin.py     # 微信测试工具
├── config/                # 配置文件
├── docs/                  # 技术文档
│   └── adapters/          # 适配器详细文档
│       └── weixin.md      # 微信适配器文档
├── scripts/               # 辅助脚本
│   ├── verify_setup.py    # 环境验证
│   └── test_all.sh        # 自动化测试
├── static/                # 管理后台静态文件
└── tests/                 # 测试套件
```

---

## 变更记录

| 日期 | 变更内容 |
|------|----------|
| 2026-03-23 | ✅ 实现微信适配器 - 支持扫码登录、消息收发、媒体上传、AES加密、完整对话能力 |
| 2026-02-05 | ✅ 实现飞书 WebSocket 长连接及双向对话 |

---

## 许可证

Apache License 2.0
