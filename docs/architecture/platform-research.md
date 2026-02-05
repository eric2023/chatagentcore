# 聊天平台接入调研

> 本文档记录国内主流聊天平台的机器人接入方式和特性，用于支持 ChatAgentCore 中间服务的架构设计。

> **重要更新：** 本项目已迁移至官方 SDK 长连接方式，不再需要公网 IP 和网络穿透。

---

## 目录

- [1. 平台接入方式对比](#1-平台接入方式对比)
- [2. 平台详细分析](#2-平台详细分析)
- [3. 接入注意事项](#3-接入注意事项)
- [4. 官方文档链接](#4-官方文档链接)

---

## 1. 平台接入方式对比

### 1.1 综合对比表

| 平台 | 机器人类型 | 消息推送方式 | 回调/响应方式 | 认证方式 | 文档完善度 |
|------|-----------|-------------|--------------|----------|-----------|
| **企业微信** | 应用机器人<br>群聊机器人 | SDK 长连接订阅 | HTTP 响应<br>主动 API 调用 | AppSecret + AccessToken<br>签名验证 | ⭐⭐⭐⭐⭐ |
| **钉钉** | 自定义机器人<br>企业内机器人 | SDK 长连接订阅<sup>1</sup> | HTTP 响应<br>主动 API 调用 | AppKey + AppSecret<br>签名验证 | ⭐⭐⭐⭐⭐ |
| **飞书** | 应用机器人<br>群机器人 | 官方 SDK 长连接 (SSE) | HTTP 响应<br>主动 API 调用 | App ID + App Secret<br>签名验证 | ⭐⭐⭐⭐⭐ |

> <sup>1</sup> 钉钉企业内机器人支持 SDK 长连接订阅事件

### 1.2 能力对比

| 特性 | 企业微信 | 钉钉 | 飞书 |
|------|---------|------|------|
| **个人号接入** | ❌ 不支持 | ⚠️ 复杂（需第三方协议） | ❌ 不支持 |
| **群机器人** | ✅ 支持 | ✅ 支持（简单 webhook） | ✅ 支持 |
| **应用机器人** | ✅ 功能完整 | ✅ 功能完整 | ✅ 功能完整 |
| **富媒体消息** | ✅ 支持 | ✅ 支持 | ✅ 支持 |
| **卡片消息** | ✅ 支持 | ✅ 支持 | ✅ 支持 |
| **消息加密** | ✅ AES 加密 | ✅ AES 加密 | ✅ AES 加密 |
| **部署要求** | 无需公网 IP (SDK 长) | 无需公网 IP (SDK 长) | 无需公网 IP (SDK 长) |

---

## 2. 平台详细分析

### 2.1 企业微信

#### 机器人类型

| 类型 | 说明 | 适用场景 |
|------|------|----------|
| **应用机器人** | 基于企业应用的机器人，功能完整 | 企业内部服务、业务流程自动化 |
| **群聊机器人** | 简单的群内消息广播 | 群通知、简单互动 |

#### 接入方式

```
┌─────────────┐      SDK        ┌─────────────┐
│   企业微信   │ ───长连接───▶ │ ChatAgent   │
│   (平台)    │   订阅事件     │  Core       │
└─────────────┘                └──────┬──────┘
                                       │
                                   HTTP 响应
                                       │
┌─────────────┐ ◀───────────────────────┘
│   企业微信   │    同步响应消息
│   (平台)    │
└─────────────┘
```

#### 认证方式

1. **企业认证**
   - CorpID（企业ID）
   - AgentID（应用ID）
   - Secret（应用密钥）

2. **签名验证**
   - Token（令牌）
   - EncodingAESKey（加密密钥）

#### 官方特性

- 支持 SDK 长连接订阅事件
- 支持应用回调 API
- 消息加密支持

---

### 2.2 钉钉

#### 机器人类型

| 类型 | 说明 | 适用场景 |
|------|------|----------|
| **自定义机器人** | 简单的群聊机器人，通过 Webhook 发送 | 监控告警、群通知 |
| **企业内机器人** | 完整功能的机器人，支持双向通信 | 企业服务、业务自动化 |
| **互动卡片机器人** | 支持卡片交互的消息机器人 | 复杂交互场景 |

#### 接入方式

**自定义机器人（Incoming Webhook）**

```
┌─────────────┐                    ┌─────────────┐
│ ChatAgent   │ ─── HTTP POST ───▶ │   钉钉     │
│   Core      │    发送消息到群    │   (平台)    │
└─────────────┘                    └─────────────┘
```

**企业内机器人（SDK 长连接）**

```
┌─────────────┐      SDK        ┌─────────────┐
│   钉钉      │ ───长连接───▶ │ ChatAgent   │
│   (平台)    │   订阅事件     │  Core       │
└─────────────┘                └──────┬──────┘
                                       │
                                   HTTP 响应
                                       │
┌─────────────┐ ◀───────────────────────┘
│   钉钉      │    同步响应消息
│   (平台)    │
└─────────────┘
```

#### 认证方式

1. **应用认证**
   - AppKey（应用Key）
   - AppSecret（应用密钥）

2. **签名验证**
   - Token（令牌）
   - AesKey（AES加密密钥）

---

### 2.3 飞书

#### 机器人类型

| 类型 | 说明 | 适用场景 |
|------|------|----------|
| **应用机器人** | 创建应用后配置机器人能力 | 企业服务、业务自动化 |
| **群机器人** | 添加到群聊的简单机器人 | 群通知、简单互动 |
| **个人机器人** | 个人使用的机器人（需特定资质） | 个人助手场景 |

#### 接入方式

**官方 SDK 长连接 (SSE) - 推荐**

```
┌─────────────┐      SDK        ┌─────────────┐
│   飞书      │ ───长连接───▶ │ ChatAgent   │
│   (平台)    │   SSE 订阅     │  Core       │
└─────────────┘                └──────┬──────┘
                                       │
                                   HTTP 响应
                                       │
┌─────────────┐ ◀───────────────────────┘
│   飞书      │    同步响应消息
│   (平台)    │
└─────────────┘
```

使用飞书官方 SDK (lark_oapi) 建立 SSE 长连接订阅消息事件。

#### 认证方式

1. **应用认证**
   - App ID（应用ID）
   - App Secret（应用密钥）

2. **签名验证**
   - 支持加解密通信

---

## 3. 接入注意事项

### 3.1 部署要求

**SDK 长连接方式无需公网 IP 或内网穿透！**

使用各平台官方 SDK 建立长连接订阅事件，可在个人电脑直接运行。

**部署优势：**
- 无需云服务器
- 无需配置路由器
- 无需内网穿透工具
- 简化运维复杂度

### 3.2 消息安全

| 平台 | 加密方式 | 安全等级 |
|------|----------|----------|
| 企业微信 | AES-256 | ⭐⭐⭐⭐⭐ |
| 钉钉 | AES-256 | ⭐⭐⭐⭐⭐ |
| 飞书 | AES-256 | ⭐⭐⭐⭐⭐ |

### 3.3 消息限流

| 平台 | 限制说明 |
|------|----------|
| 企业微信 | 每分钟 20 万条消息（企业级） |
| 钉钉 | 每分钟 20 万次调用（企业级） |
| 飞书 | 每分钟 20 万次调用（企业级） |

### 3.4 消息格式各平台差异

```json
// 企业微信消息格式示例
{
  "ToUserName": "ww123456789",
  "FromUserName": "User123",
  "CreateTime": 1700000000,
  "MsgType": "text",
  "Content": "Hello",
  "MsgId": "123456789"
}

// 钉钉消息格式示例
{
  "msgId": "msg123",
  "createAt": 1700000000,
  "conversationType": "2",
  "conversationId": "cid123",
  "senderId": "user123",
  "senderNick": "用户昵称",
  "chatbotUserId": "bot123",
  "msgtype": "text",
  "content": {
    "content": "Hello"
  }
}

// 飞书消息格式示例
{
  "header": {
    "event_id": "event123",
    "event_type": "im.message.receive_v1",
    "create_time": 1700000000,
    "token": "verif_token",
    "app_id": "app123"
  },
  "event": {
    "sender": {
      "sender_id": {
        "open_id": "ou_123"
      },
      "sender_type": "user"
    },
    "message": {
      "message_id": "om_123",
      "chat_type": "group",
      "msg_type": "text",
      "content": "{\"text\":\"Hello\"}"
    }
  }
}
```

---

## 4. 官方文档链接

### 4.1 企业微信

| 文档 | 链接 |
|------|------|
| 官方开发平台 | https://developer.work.weixin.qq.com |
| 机器人开发文档 | https://developer.work.weixin.qq.com/document/path/91770 |
| 企业内部应用回调 | https://developer.work.weixin.qq.com/document/path/90930 |
| 群聊机器人 | https://developer.work.weixin.qq.com/document/path/90238 |
| 消息加解密 | https://developer.work.weixin.qq.com/document/path/90512 |

### 4.2 钉钉

| 文档 | 链接 |
|------|------|
| 官方开放平台 | https://open.dingtalk.com/document-org |
| 企业内机器人 | https://open.dingtalk.com/document-org/robots-overview |
| 自定义机器人 | https://open.dingtalk.com/document/group/custom-robot-access |
| SDK 长连接订阅 | https://open.dingtalk.com/document/org-applications/create-outgoing-robot |
| 消息加解密 | https://open.dingtalk.com/document/custom-bot/encrypt |

### 4.3 飞书

| 文档 | 链接 |
|------|------|
| 官方开放平台 | https://open.feishu.cn/document |
| 机器人开发文档 | https://open.feishu.cn/document/server-docs/bot-v3/add-custom-bot |
| 服务端 SDK | https://open.feishu.cn/document/server-docs/server-side-sdk |
| 事件流 API | https://open.feishu.cn/document/server-docs/event-subscription-guide/message-mode/event-listen-overview |
| 接收消息 | https://open.feishu.cn/document/server-docs/event-subscription-guide/message-mode/event-listen-im |
| 消息加解密 | https://open.feishu.cn/document/server-docs/event-subscription-guide/message-mode/encryption |

## 5. SDK 参考

### 5.1 Python SDK

| SDK | 平台 | GitHub |
|-----|------|--------|
| enterprise-wechat-sdk | 企业微信（官方） | https://github.com/Wechat-Work-Python |
| dingtalk-sdk | 钉钉（官方） | https://github.com/open-dingtalk/p钉钉 |
| lark-oapi | 飞书（官方） | https://github.com/larksuite/oapi-sdk-python |

### 5.2 其他语言 SDK

| 语言 | 企业微信 | 钉钉 | 飞书 |
|------|---------|------|------|
| Java | WxWork-Java-SDK | dingtalk-sdk | lark-oapi-sdk-java |
| Node.js | 企业微信机器人 SDK | dingtalk-sdk | lark-oapi-sdk-nodejs |
| Go | 企业微信 Go SDK | dingtalk-go-sdk | lark-oapi-sdk-go |

---

**文档版本:** 2.0.0 (SDK 长连接版)
**最后更新:** 2026-02-04
**状态:** 已确认，已迁移至 SDK 长连接方式
