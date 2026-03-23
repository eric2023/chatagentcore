"""微信媒体数据模型

基于 openclaw-weixin 插件的媒体相关协议定义。
"""

from typing import Optional
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 媒体类型常量
# ---------------------------------------------------------------------------

class MediaType:
    """上传媒体类型"""
    IMAGE = 1
    VIDEO = 2
    FILE = 3
    VOICE = 4


# ---------------------------------------------------------------------------
# 媒体上传下载请求/响应模型
# ---------------------------------------------------------------------------


class GetUploadUrlReq(BaseModel):
    """获取上传 URL 请求"""
    filekey: Optional[str] = Field(None, description="文件标识")
    media_type: Optional[int] = Field(None, description="媒体类型: 1=IMAGE, 2=VIDEO, 3=FILE, 4=VOICE")
    to_user_id: Optional[str] = Field(None, description="目标用户 ID")
    rawsize: Optional[int] = Field(None, description="原文件明文大小")
    rawfilemd5: Optional[str] = Field(None, description="原文件明文 MD5")
    filesize: Optional[int] = Field(None, description="原文件密文大小（AES-128-ECB 加密后）")
    thumb_rawsize: Optional[int] = Field(None, description="缩略图明文大小（IMAGE/VIDEO 时必填）")
    thumb_rawfilemd5: Optional[str] = Field(None, description="缩略图明文 MD5（IMAGE/VIDEO 时必填）")
    thumb_filesize: Optional[int] = Field(None, description="缩略图密文大小（IMAGE/VIDEO 时必填）")
    no_need_thumb: Optional[bool] = Field(None, description="不需要缩略图上传 URL，默认 false")
    aeskey: Optional[str] = Field(None, description="加密 key")


class GetUploadUrlResp(BaseModel):
    """获取上传 URL 响应"""
    upload_param: Optional[str] = Field(None, description="原图上传加密参数")
    thumb_upload_param: Optional[str] = Field(None, description="缩略图上传加密参数，无缩略图时为空")


class UploadMediaInfo(BaseModel):
    """媒体上传信息"""
    file_path: str = Field(..., description="文件路径")
    media_type: int = Field(..., description="媒体类型")
    to_user_id: str = Field(..., description="目标用户 ID")
    text: Optional[str] = Field(None, description="附带的文本描述")


class DownloadMediaInfo(BaseModel):
    """媒体下载信息"""
    encrypt_query_param: str = Field(..., description="加密查询参数")
    aes_key: str = Field(..., description="AES 密钥 (base64)")
    media_type: int = Field(..., description="媒体类型")
