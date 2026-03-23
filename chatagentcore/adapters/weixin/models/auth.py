"""微信认证数据模型

基于 openclaw-weixin 插件的认证相关协议定义。
"""

from typing import Optional, Dict, Any
from pydantic import BaseModel, Field

# 导入常量
from ..constants import DEFAULT_ILINK_BOT_TYPE, QrcodeStatusType as _QrcodeStatusType


# ---------------------------------------------------------------------------
# 导出常量
# ---------------------------------------------------------------------------

DEFAULT_ILINK_BOT_TYPE = DEFAULT_ILINK_BOT_TYPE


class QrcodeStatusType:
    """二维码状态类型"""
    WAIT = _QrcodeStatusType.WAIT
    SCANED = _QrcodeStatusType.SCANED
    CONFIRMED = _QrcodeStatusType.CONFIRMED
    EXPIRED = _QrcodeStatusType.EXPIRED


# ---------------------------------------------------------------------------
# 认证请求/响应模型
# ---------------------------------------------------------------------------


class QrcodeResponse(BaseModel):
    """获取二维码响应"""
    qrcode: Optional[str] = Field(None, description="二维码内容")
    qrcode_img_content: Optional[str] = Field(None, description="二维码图片 URL")


class QrcodeStatus(BaseModel):
    """二维码状态响应"""
    status: str = Field(..., description="状态: wait|scaned|confirmed|expired")
    bot_token: Optional[str] = Field(None, description="Bot Token（确认后返回）")
    ilink_bot_id: Optional[str] = Field(None, description="iLink Bot ID（确认后返回）")
    baseurl: Optional[str] = Field(None, description="基础 URL（确认后返回）")
    ilink_user_id: Optional[str] = Field(None, description="iLink 用户 ID（确认后返回，扫码的用户）")


class LoginResult(BaseModel):
    """登录结果"""
    success: bool = Field(..., description="是否登录成功")
    message: str = Field(..., description="结果描述")
    bot_token: Optional[str] = Field(None, description="Bot Token（成功时返回）")
    account_id: Optional[str] = Field(None, description="账号 ID（成功时返回）")
    base_url: Optional[str] = Field(None, description="基础 URL（成功时返回）")
    user_id: Optional[str] = Field(None, description="用户 ID（成功时返回）")


class WeixinAccountData(BaseModel):
    """微信账号数据（持久化）"""
    token: Optional[str] = Field(None, description="Bot Token")
    saved_at: Optional[str] = Field(None, description="保存时间 (ISO 8601)")
    base_url: Optional[str] = Field(None, description="基础 URL")
    user_id: Optional[str] = Field(None, description="用户 ID")
