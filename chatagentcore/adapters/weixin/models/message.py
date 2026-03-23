"""微信消息数据模型

基于 openclaw-weixin 插件的协议定义。
参考: openclaw-weixin/src/api/types.ts
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# 常量定义
# ---------------------------------------------------------------------------

class MessageType:
    """消息类型"""
    NONE = 0
    USER = 1
    BOT = 2


class MessageItemType:
    """消息条目类型"""
    NONE = 0
    TEXT = 1
    IMAGE = 2
    VOICE = 3
    FILE = 4
    VIDEO = 5


class MessageState:
    """消息状态"""
    NEW = 0
    GENERATING = 1
    FINISH = 2


# ---------------------------------------------------------------------------
# 基础数据结构
# ---------------------------------------------------------------------------

class BaseInfo(BaseModel):
    """请求元数据，附加到每个 CGI 请求"""
    channel_version: Optional[str] = Field(None, description="渠道版本")


class TextItem(BaseModel):
    """文本消息内容"""
    text: Optional[str] = Field(None, description="文本内容")


class CDNMedia(BaseModel):
    """CDN 媒体引用

    所有媒体类型（图片/语音/文件/视频）通过 CDN 传输，使用 AES-128-ECB 加密。
    """
    encrypt_query_param: Optional[str] = Field(None, description="CDN 下载/上传的加密参数")
    aes_key: Optional[str] = Field(None, description="base64 编码的 AES-128 密钥")
    encrypt_type: Optional[int] = Field(None, description="加密类型: 0=只加密fileid, 1=打包缩略图/中图等信息")


class ImageItem(BaseModel):
    """图片消息"""
    media: Optional[CDNMedia] = Field(None, description="原图 CDN 引用")
    thumb_media: Optional[CDNMedia] = Field(None, description="缩略图 CDN 引用")
    aeskey: Optional[str] = Field(None, description="Raw AES-128 key as hex string (16 bytes)")
    url: Optional[str] = Field(None, description="图片 URL")
    mid_size: Optional[int] = Field(None, description="中图大小")
    thumb_size: Optional[int] = Field(None, description="缩略图大小")
    thumb_height: Optional[int] = Field(None, description="缩略图高度")
    thumb_width: Optional[int] = Field(None, description="缩略图宽度")
    hd_size: Optional[int] = Field(None, description="高清图大小")


class VoiceItem(BaseModel):
    """语音消息"""
    media: Optional[CDNMedia] = Field(None, description="语音 CDN 引用")
    encode_type: Optional[int] = Field(None, description="语音编码类型: 1=pcm 2=adpcm 3=feature 4=speex 5=amr 6=silk 7=mp3 8=ogg-speex")
    bits_per_sample: Optional[int] = Field(None, description="每样本比特数")
    sample_rate: Optional[int] = Field(None, description="采样率 (Hz)")
    playtime: Optional[int] = Field(None, description="语音长度 (毫秒)")
    text: Optional[str] = Field(None, description="语音转文字内容")


class FileItem(BaseModel):
    """文件消息"""
    media: Optional[CDNMedia] = Field(None, description="文件 CDN 引用")
    file_name: Optional[str] = Field(None, description="文件名")
    md5: Optional[str] = Field(None, description="MD5")
    len: Optional[str] = Field(None, description="文件长度")


class VideoItem(BaseModel):
    """视频消息"""
    media: Optional[CDNMedia] = Field(None, description="视频 CDN 引用")
    video_size: Optional[int] = Field(None, description="视频大小")
    play_length: Optional[int] = Field(None, description="播放长度")
    video_md5: Optional[str] = Field(None, description="视频 MD5")
    thumb_media: Optional[CDNMedia] = Field(None, description="缩略图 CDN 引用")
    thumb_size: Optional[int] = Field(None, description="缩略图大小")
    thumb_height: Optional[int] = Field(None, description="缩略图高度")
    thumb_width: Optional[int] = Field(None, description="缩略图宽度")


class RefMessage(BaseModel):
    """引用消息"""
    message_item: Optional["MessageItem"] = Field(None, description="被引用的消息内容")
    title: Optional[str] = Field(None, description="摘要")


class MessageItem(BaseModel):
    """消息条目"""
    type: Optional[int] = Field(None, description="消息类型: 1=TEXT 2=IMAGE 3=VOICE 4=FILE 5=VIDEO")
    create_time_ms: Optional[int] = Field(None, description="创建时间戳 (毫秒)")
    update_time_ms: Optional[int] = Field(None, description="更新时间戳 (毫秒)")
    is_completed: Optional[bool] = Field(None, description="是否完成")
    msg_id: Optional[str] = Field(None, description="消息 ID")
    ref_msg: Optional[RefMessage] = Field(None, description="引用消息")
    text_item: Optional[TextItem] = Field(None, description="文本内容")
    image_item: Optional[ImageItem] = Field(None, description="图片内容")
    voice_item: Optional[VoiceItem] = Field(None, description="语音内容")
    file_item: Optional[FileItem] = Field(None, description="文件内容")
    video_item: Optional[VideoItem] = Field(None, description="视频内容")

    # 更新前向引用
    model_config = {"arbitrary_types_allowed": True}


class WeixinMessage(BaseModel):
    """统一微信消息结构 (proto: WeixinMessage)"""
    seq: Optional[int] = Field(None, description="消息序列号")
    message_id: Optional[int] = Field(None, description="消息唯一 ID")
    from_user_id: Optional[str] = Field(None, description="发送者 ID")
    to_user_id: Optional[str] = Field(None, description="接收者 ID")
    client_id: Optional[str] = Field(None, description="客户端 ID")
    create_time_ms: Optional[int] = Field(None, description="创建时间戳 (毫秒)")
    update_time_ms: Optional[int] = Field(None, description="更新时间戳 (毫秒)")
    delete_time_ms: Optional[int] = Field(None, description="删除时间戳 (毫秒)")
    session_id: Optional[str] = Field(None, description="会话 ID")
    group_id: Optional[str] = Field(None, description="群 ID")
    message_type: Optional[int] = Field(None, description="消息类型: 1=USER 2=BOT")
    message_state: Optional[int] = Field(None, description="消息状态: 0=NEW 1=GENERATING 2=FINISH")
    item_list: Optional[List[MessageItem]] = Field(None, description="消息内容列表")
    context_token: Optional[str] = Field(None, description="会话上下文令牌，回复时需回传")


# ---------------------------------------------------------------------------
# API 请求/响应模型
# ---------------------------------------------------------------------------


class GetUpdatesReq(BaseModel):
    """获取更新请求（长轮询）"""
    get_updates_buf: str = Field("", description="上次响应返回的同步游标，首次请求传空字符串")


class GetUpdatesResp(BaseModel):
    """获取更新响应"""
    ret: Optional[int] = Field(None, description="返回码，0 = 成功")
    errcode: Optional[int] = Field(None, description="错误码（如 -14 = 会话超时）")
    errmsg: Optional[str] = Field(None, description="错误描述")
    msgs: Optional[List[WeixinMessage]] = Field(None, description="消息列表")
    get_updates_buf: Optional[str] = Field(None, description="新的同步游标，下次请求时回传")
    longpolling_timeout_ms: Optional[int] = Field(None, description="服务端建议的下次长轮询超时 (ms)")


class SendMessageReq(BaseModel):
    """发送消息请求（ wraps 一个 WeixinMessage）"""
    msg: Optional[WeixinMessage] = Field(None, description="要发送的消息")


class SendMessageResp(BaseModel):
    """发送消息响应"""
    # 空响应
    pass


class TypingStatus:
    """输入状态"""
    TYPING = 1
    CANCEL = 2


class SendTypingReq(BaseModel):
    """发送输入状态请求"""
    ilink_user_id: Optional[str] = Field(None, description="用户 ID")
    typing_ticket: Optional[str] = Field(None, description="输入状态票据")
    status: Optional[int] = Field(None, description="1=typing (default), 2=cancel typing")


class SendTypingResp(BaseModel):
    """发送输入状态响应"""
    ret: Optional[int] = Field(None, description="返回码")
    errmsg: Optional[str] = Field(None, description="错误描述")


class GetConfigResp(BaseModel):
    """获取配置响应"""
    ret: Optional[int] = Field(None, description="返回码")
    errmsg: Optional[str] = Field(None, description="错误描述")
    typing_ticket: Optional[str] = Field(None, description="base64 编码的 typing ticket")
