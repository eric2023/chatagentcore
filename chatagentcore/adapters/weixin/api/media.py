"""媒体 API

提供媒体文件的上传下载功能，包括 CDN 上传 URL 获取、加密解密等。
参考: openclaw-weixin/src/cdn/
"""

import json
import os
import tempfile
from typing import Optional, BinaryIO

from loguru import logger

from .client import WeixinHTTPClient, DEFAULT_CDN_BASE_URL
from ..models.media import (
    MediaType,
    GetUploadUrlReq,
    GetUploadUrlResp,
)
from ..models.message import CDNMedia, MessageItem, MessageItemType
from ..crypto.aes_ecb import (
    encrypt_aes_ecb,
    decrypt_aes_ecb,
    aes_ecb_padded_size,
    parse_aes_key,
    compute_md5,
    compute_md5_file,
)
from ..utils.helpers import build_base_info


# ---------------------------------------------------------------------------
# 媒体 API
# ---------------------------------------------------------------------------


class MediaAPI:
    """微信媒体 API

    提供媒体文件的上传下载功能。
    """

    def __init__(
        self,
        base_url: str = "https://ilinkai.weixin.qq.com",
        cdn_base_url: str = DEFAULT_CDN_BASE_URL,
        token: Optional[str] = None,
        client: Optional[WeixinHTTPClient] = None,
    ):
        """初始化媒体 API

        Args:
            base_url: API 基础 URL
            cdn_base_url: CDN 基础 URL
            token: Bot Token
            client: HTTP 客户端（可选）
        """
        self.base_url = base_url
        self.cdn_base_url = cdn_base_url
        self.token = token

        if client:
            self.client = client
        else:
            self.client = WeixinHTTPClient(base_url=base_url, token=token)

    def update_token(self, token: str) -> None:
        """更新 Token

        Args:
            token: 新的 Token
        """
        self.token = token
        self.client.update_token(token)

    async def get_upload_url(
        self,
        req: GetUploadUrlReq,
    ) -> GetUploadUrlResp:
        """获取 CDN 上传预签名 URL

        Args:
            req: 上传请求

        Returns:
            上传 URL 响应

        Raises:
            Exception: 获取上传 URL 失败
        """
        payload = {
            "filekey": req.filekey,
            "media_type": req.media_type,
            "to_user_id": req.to_user_id,
            "rawsize": req.rawsize,
            "rawfilemd5": req.rawfilemd5,
            "filesize": req.filesize,
            "thumb_rawsize": req.thumb_rawsize,
            "thumb_rawfilemd5": req.thumb_rawfilemd5,
            "thumb_filesize": req.thumb_filesize,
            "no_need_thumb": req.no_need_thumb,
            "aeskey": req.aeskey,
            "base_info": build_base_info(),
        }

        # 移除 None 值
        payload = {k: v for k, v in payload.items() if v is not None}

        try:
            response_text = await self.client.post(
                "ilink/bot/getuploadurl",
                data=payload,
                timeout_ms=15000,
                label="getUploadUrl",
            )

            response_dict = json.loads(response_text)

            return GetUploadUrlResp(
                upload_param=response_dict.get("upload_param", ""),
                thumb_upload_param=response_dict.get("thumb_upload_param", ""),
            )

        except Exception as e:
            logger.error(f"getUploadUrl 失败: {e}")
            raise Exception(f"获取上传 URL 失败: {e}") from e

    async def upload_to_cdn(
        self,
        url: str,
        data: bytes,
        content_type: str = "application/octet-stream",
    ) -> None:
        """上传数据到 CDN

        Args:
            url: CDN 上传 URL
            data: 要上传的数据（已加密）
            content_type: 内容类型

        Raises:
            Exception: 上传失败
        """
        try:
            client = await self.client._get_client()

            logger.debug(f"上传到 CDN: url={url[:80]}..., size={len(data)} bytes")

            response = await client.put(
                url,
                content=data,
                headers={"Content-Type": content_type},
                timeout=60.0,
            )

            if not response.is_success:
                error_text = response.text
                logger.error(f"CDN 上传失败: {response.status_code}, {error_text}")
                raise Exception(f"CDN 上传失败: {response.status_code}, {error_text}")

            logger.debug(f"CDN 上传成功: {response.status_code}")

        except Exception as e:
            logger.error(f"upload_to_cdn 失败: {e}")
            raise Exception(f"上传到 CDN 失败: {e}") from e

    async def download_from_cdn(
        self,
        encrypt_query_param: str,
        aes_key: bytes,
    ) -> bytes:
        """从 CDN 下载并解密媒体文件

        Args:
            encrypt_query_param: 加密查询参数
            aes_key: AES 密钥（16 字节）

        Returns:
            解密后的数据

        Raises:
            Exception: 下载或解密失败
        """
        try:
            # 构建 CDN URL
            url = f"{self.cdn_base_url}/{encrypt_query_param}"

            logger.debug(f"从 CDN 下载: url={url[:80]}...")

            client = await self.client._get_client()

            response = await client.get(url, timeout=60.0)

            if not response.is_success:
                error_text = response.text
                logger.error(f"CDN 下载失败: {response.status_code}, {error_text}")
                raise Exception(f"CDN 下载失败: {response.status_code}, {error_text}")

            encrypted_data = response.content
            logger.debug(f"CDN 下载成功: size={len(encrypted_data)} bytes")

            # 解密
            decrypted_data = decrypt_aes_ecb(encrypted_data, aes_key)
            logger.debug(f"解密成功: size={len(decrypted_data)} bytes")

            return decrypted_data

        except Exception as e:
            logger.error(f"download_from_cdn 失败: {e}")
            raise Exception(f"从 CDN 下载失败: {e}") from e

    async def upload_media(
        self,
        file_path: str,
        to_user_id: str,
        media_type: int,
        context_token: Optional[str] = None,
        thumbnail_path: Optional[str] = None,
    ) -> CDNMedia:
        """完整的媒体上传流程

        1. 读取文件并计算 MD5
        2. 使用 AES-128-ECB 加密
        3. 获取上传 URL
        4. 上传到 CDN

        Args:
            file_path: 文件路径
            to_user_id: 目标用户 ID
            media_type: 媒体类型
            context_token: 上下文令牌
            thumbnail_path: 缩略图路径（图片/视频时可选）

        Returns:
            CDN 媒体引用

        Raises:
            Exception: 上传失败
        """
        try:
            # 1. 读取文件
            with open(file_path, "rb") as f:
                raw_data = f.read()

            raw_size = len(raw_data)
            raw_md5 = compute_md5(raw_data)

            logger.info(
                f"准备上传媒体: type={media_type}, file={os.path.basename(file_path)}, size={raw_size}"
            )

            # 2. 生成 AES 密钥（16 字节）
            import secrets

            aes_key = secrets.token_bytes(16)
            aes_key_b64 = aes_key.hex()  # hex 编码（微信格式要求）

            # 3. 加密文件
            encrypted_data = encrypt_aes_ecb(raw_data, aes_key)
            encrypted_size = len(encrypted_data)

            logger.debug(
                f"媒体加密完成: raw={raw_size} → encrypted={encrypted_size}"
            )

            # 4. 处理缩略图（图片/视频）
            thumb_raw_size = None
            thumb_raw_md5 = None
            thumb_encrypted_data = None
            thumb_encrypted_size = None

            if thumbnail_path and os.path.exists(thumbnail_path):
                with open(thumbnail_path, "rb") as f:
                    thumb_raw_data = f.read()

                thumb_raw_size = len(thumb_raw_data)
                thumb_raw_md5 = compute_md5(thumb_raw_data)
                thumb_encrypted_data = encrypt_aes_ecb(thumb_raw_data, aes_key)
                thumb_encrypted_size = len(thumb_encrypted_data)

                logger.debug(
                    f"缩略图处理完成: raw={thumb_raw_size} → encrypted={thumb_encrypted_size}"
                )

            # 5. 获取上传 URL
            upload_req = GetUploadUrlReq(
                filekey="",  # 可选，通常为空
                media_type=media_type,
                to_user_id=to_user_id,
                rawsize=raw_size,
                rawfilemd5=raw_md5,
                filesize=encrypted_size,
                thumb_rawsize=thumb_raw_size,
                thumb_rawfilemd5=thumb_raw_md5,
                thumb_filesize=thumb_encrypted_size,
                no_need_thumb=thumbnail_path is None,
                aeskey=aes_key_b64,
            )

            upload_resp = await self.get_upload_url(upload_req)

            logger.debug(f"获取上传 URL 成功")

            # 6. 上传原图
            if upload_resp.upload_param:
                await self.upload_to_cdn(upload_resp.upload_param, encrypted_data)
                logger.debug("原图上传成功")

            # 7. 上传缩略图
            if thumb_encrypted_data and upload_resp.thumb_upload_param:
                await self.upload_to_cdn(
                    upload_resp.thumb_upload_param, thumb_encrypted_data
                )
                logger.debug("缩略图上传成功")

            # 8. 构建 CDN 媒体引用
            media = CDNMedia(
                encrypt_query_param=upload_resp.upload_param,
                aes_key=aes_key_b64,
                encrypt_type=1,
            )

            logger.info(f"媒体上传完成: encrypt_param={upload_resp.upload_param[:50] if upload_resp.upload_param else '(empty)'}...")

            return media

        except Exception as e:
            logger.error(f"upload_media 失败: {e}")
            raise Exception(f"媒体上传失败: {e}") from e

    async def download_media(
        self,
        media: CDNMedia,
        save_path: Optional[str] = None,
    ) -> bytes:
        """下载媒体文件

        Args:
            media: CDN 媒体引用
            save_path: 保存路径（可选，不提供则不保存）

        Returns:
            解密后的数据
        """
        if not media.encrypt_query_param:
            raise ValueError("CDN 媒体引用缺少 encrypt_query_param")

        if not media.aes_key:
            raise ValueError("CDN 媒体引用缺少 aes_key")

        # 解析密钥
        aes_key = parse_aes_key(media.aes_key)

        # 下载并解密
        data = await self.download_from_cdn(media.encrypt_query_param, aes_key)

        # 保存到文件
        if save_path:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "wb") as f:
                f.write(data)
            logger.debug(f"媒体已保存: {save_path}")

        return data

    async def close(self) -> None:
        """关闭客户端"""
        await self.client.close()
