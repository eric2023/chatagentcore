"""AES-128-ECB 加密解密工具

基于 openclaw-weixin 插件的加密实现。
参考: openclaw-weixin/src/cdn/aes_ecb.ts

微信媒体文件使用 AES-128-ECB 加密进行传输。
"""

import base64
import hashlib
from typing import Union

from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend


# ---------------------------------------------------------------------------
# AES-128-ECB 加密解密
# ---------------------------------------------------------------------------

def encrypt_aes_ecb(plaintext: bytes, key: bytes) -> bytes:
    """使用 AES-128-ECB 加密明文（PKCS7 填充）

    Args:
        plaintext: 待加密的明文
        key: 16 字节的 AES 密钥

    Returns:
        加密后的密文
    """
    # 创建 AES-ECB 加密器
    cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
    encryptor = cipher.encryptor()

    # PKCS7 填充
    padder = padding.PKCS7(128).padder()
    padded_data = padder.update(plaintext) + padder.finalize()

    # 加密
    ciphertext = encryptor.update(padded_data) + encryptor.finalize()
    return ciphertext


def decrypt_aes_ecb(ciphertext: bytes, key: bytes) -> bytes:
    """使用 AES-128-ECB 解密密文（PKCS7 填充）

    Args:
        ciphertext: 待解密的密文
        key: 16 字节的 AES 密钥

    Returns:
        解密后的明文
    """
    # 创建 AES-ECB 解密器
    cipher = Cipher(algorithms.AES(key), modes.ECB(), backend=default_backend())
    decryptor = cipher.decryptor()

    # 解密
    padded_data = decryptor.update(ciphertext) + decryptor.finalize()

    # 移除 PKCS7 填充
    unpadder = padding.PKCS7(128).unpadder()
    plaintext = unpadder.update(padded_data) + unpadder.finalize()
    return plaintext


# ---------------------------------------------------------------------------
# 大小计算
# ---------------------------------------------------------------------------

def aes_ecb_padded_size(plaintext_size: int) -> int:
    """计算 AES-128-ECB 加密后的密文大小（PKCS7 填充到 16 字节边界）

    Args:
        plaintext_size: 明文大小（字节数）

    Returns:
        加密后的密文大小（字节数）
    """
    return ((plaintext_size + 1) // 16) * 16


# ---------------------------------------------------------------------------
# 密钥解析
# ---------------------------------------------------------------------------

def parse_aes_key(aes_key_base64: str) -> bytes:
    """解析 AES 密钥的多种编码格式

    微信的 aes_key 字段有两种编码：
    1. 直接 base64 编码 16 字节密钥（图片）
    2. base64 编码 32 字符 hex 字符串，再 hex 解码为 16 字节（文件/语音/视频）

    Args:
        aes_key_base64: base64 编码的密钥

    Returns:
        解析后的 16 字节 AES 密钥

    Raises:
        ValueError: 密钥格式不正确
    """
    # 首先进行 base64 解码
    decoded = base64.b64decode(aes_key_base64)

    # 情况 1: 直接是 16 字节密钥
    if len(decoded) == 16:
        return decoded

    # 情况 2: 是 32 字符的 hex 字符串（被 base64 编码过）
    if len(decoded) == 32:
        try:
            hex_str = decoded.decode('ascii')
            if len(hex_str) == 32 and all(c in '0123456789abcdefABCDEF' for c in hex_str):
                # hex 字符串 → raw bytes
                return bytes.fromhex(hex_str)
        except (UnicodeDecodeError, ValueError):
            pass

    raise ValueError(
        f"AES 密钥格式不正确: base64 解析后得到 {len(decoded)} 字节，"
        f"期望 16 字节或 32 字符 hex 字符串 (base64=\"{aes_key_base64}\")"
    )


# ---------------------------------------------------------------------------
# MD5 计算
# ---------------------------------------------------------------------------

def compute_md5(data: bytes) -> str:
    """计算数据的 MD5 哈希值

    Args:
        data: 待计算的数据

    Returns:
        MD5 哈希值（小写 hex 字符串）
    """
    md5_hash = hashlib.md5()
    md5_hash.update(data)
    return md5_hash.hexdigest()


def compute_md5_file(file_path: str) -> str:
    """计算文件的 MD5 哈希值

    Args:
        file_path: 文件路径

    Returns:
        MD5 哈希值（小写 hex 字符串）
    """
    md5_hash = hashlib.md5()
    with open(file_path, 'rb') as f:
        for chunk in iter(lambda: f.read(8192), b''):
            md5_hash.update(chunk)
    return md5_hash.hexdigest()
