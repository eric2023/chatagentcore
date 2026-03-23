# 微信适配器

微信适配器支持通过 iLink AI 微信聊天 API 接入微信，提供完整的聊天功能。

## 功能特性

- ✅ 扫码登录
- ✅ 长轮询接收消息
- ✅ 发送文本消息
- ✅ 发送图片/视频/文件/语音消息
- ✅ 媒体文件 AES-128-ECB 加密
- ✅ 输入状态指示
- ✅ 会话管理
- ✅ Token 持久化存储

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

或者只安装可选依赖：

```bash
pip install chatagentcore[weixin]
```

### 2. 扫码登录

```bash
# 方式 1: 使用测试工具
python cli/test_weixin.py login

# 方式 2: 在代码中使用
from chatagentcore.adapters.weixin import WeixinAdapter

config = {
    "account_id": "default",
    "base_url": "https://ilinkai.weixin.qq.com",
    "cdn_base_url": "https://novac2c.cdn.weixin.qq.com/c2c",
    "state_dir": "~/.openclaw-weixin",
}

adapter = WeixinAdapter(config)
await adapter.login_with_qr()
```

### 3. 接收消息

```bash
# 使用测试工具接收消息（默认 60 秒）
python cli/test_weixin.py receive --duration 120

# 在代码中使用
async def message_handler(msg):
    print(f"收到消息: {msg}")

adapter.set_message_handler(message_handler)
await adapter.initialize()
```

### 4. 发送消息

```bash
# 使用测试工具发送消息
python cli/test_weixin.py send --to "xxx@im.wechat" --text "你好，世界！"

# 在代码中使用
await adapter.send_text_message(to="xxx@im.wechat", text="你好，世界！")
```

## 配置说明

### 适配器配置

```python
config = {
    # 账号标识（如 "default"）
    "account_id": "default",

    # API 基础 URL
    "base_url": "https://ilinkai.weixin.qq.com",

    # CDN 基础 URL
    "cdn_base_url": "https://novac2c.cdn.weixin.qq.com/c2c",

    # Bot Token（可选，首次登录后自动保存）
    "token": "your_bot_token",

    # 状态目录（可选，默认 ~/.openclaw-weixin）
    "state_dir": "~/.openclaw-weixin",
}
```

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `WEIXIN_BASE_URL` | API 基础 URL | https://ilinkai.weixin.qq.com |
| `WEIXIN_CDN_BASE_URL` | CDN 基础 URL | https://novac2c.cdn.weixin.qq.com/c2c |
| `WEIXIN_STATE_DIR` | 状态目录 | ~/.openclaw-weixin |

## API 参考

### WeixinAdapter

微信适配器主类，继承自 BaseAdapter。

#### 方法

##### `__init__(config: Dict[str, Any])`

初始化适配器。

##### `async login_with_qr(timeout_ms: int, display_callback) -> Dict`

扫码登录。

**参数：**
- `timeout_ms`: 超时时间（毫秒），默认 300000（5 分钟）
- `display_callback`: 二维码显示回调函数

**返回：**
- `{"success": bool, "message": str, "bot_token": str, "account_id": str, "user_id": str}`

##### `async send_message(to, message_type, content, conversation_type) -> str`

发送消息。

**参数：**
- `to`: 接收者 ID（格式：xxx@im.wechat）
- `message_type`: 消息类型（"text"、"image"、"video"、"file"）
- `content`: 消息内容
- `conversation_type`: 会话类型（默认 "user"）

**返回：** 消息 ID

##### `async send_text_message(to, text) -> str`

发送文本消息（便捷方法）。

##### `async send_media_message(to, media_path, caption, thumbnail_path) -> str`

发送媒体消息（图片、视频、文件）。

##### `set_message_handler(handler: Callable)`

设置消息处理器。

**参数：**
- `handler`: 处理函数，接收 Message 对象

### 统一消息格式 (Message)

```python
{
    "platform": "weixin",
    "message_id": "msg_id",
    "sender": {"id": "xxx@im.wechat", "name": ""},
    "conversation": {"id": "session_id", "type": "user"},
    "content": {
        "type": "text",
        "text": "消息内容",
        "has_media": False,
        "media": {},
    },
    "timestamp": 1711234567,
}
```

## 协议说明

本适配器基于腾讯官方 openclaw-weixin 插件实现，使用 iLink AI 微信聊天 API。

### 核心接口

| 接口 | 方法 | 说明 |
|------|------|------|
| `getupdates` | POST | 长轮询获取新消息 |
| `sendmessage` | POST | 发送消息（文本/图片/视频/文件） |
| `getuploadurl` | POST | 获取 CDN 上传预签名 URL |
| `getconfig` | POST | 获取账号配置（typing ticket 等） |
| `sendtyping` | POST | 发送/取消输入状态指示 |

### 请求 Headers

```http
Content-Type: application/json
AuthorizationType: ilink_bot_token
Authorization: Bearer <token>
X-WECHAT-UIN: <random_base64>
```

### 媒体加密

所有媒体文件使用 AES-128-ECB 加密：
- 密钥长度：16 字节
- 填充方式：PKCS7
- 加密文件上传到 CDN

### 长轮询

- 默认超时：35 秒
- 返回格式：JSON
- 游标机制：使用 `get_updates_buf` 防止消息重复

## 常见问题

### 1. 登录后 Token 仍为空

Token 会自动保存到 `~/.openclaw-weixin/accounts/{account_id}.json`。请检查文件是否存在。

### 2. 发送消息时提示 "未找到上下文令牌"

需要先接收一条来自目标用户的消息，建立会话（context_token）。

### 3. 长轮询超时

长轮询超时是正常现象，会自动重连。如果一直无法接收消息，请检查：
- Token 是否正确
- 网络连接是否正常
- API 服务是否可用

### 4. 会话过期

如果会话过期（错误码 -14），适配器会自动暂停 5 分钟后重试。

## 开发参考

- [openclaw-weixin 插件源码](https://github.com/anthropics/openclaw)
- [openclaw-weixin 协议分析](openclaw-weixin-analysis.md)
- API 基础 URL: https://ilinkai.weixin.qq.com
- CDN 基础 URL: https://novac2c.cdn.weixin.qq.com/c2c

## 许可证

Apache License 2.0
