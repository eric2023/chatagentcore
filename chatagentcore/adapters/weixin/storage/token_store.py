"""Token 存储

安全持久化登录 Token。
参考: openclaw-weixin/src/auth/accounts.ts
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, List
from datetime import datetime

from loguru import logger

from ..models.auth import WeixinAccountData
from ..utils.helpers import normalize_account_id


# ---------------------------------------------------------------------------
# Token 存储
# ---------------------------------------------------------------------------


class TokenStore:
    """Token 持久化存储

    将 Token 安全地保存到文件系统。
    文件权限：0o600（仅所有者可读写）。
    """

    def __init__(self, state_dir: Optional[str] = None):
        """初始化 Token 存储

        Args:
            state_dir: 状态目录，默认为 ~/.openclaw-weixin
        """
        if state_dir is None:
            home = Path.home()
            state_dir = home / ".openclaw-weixin"

        self.state_dir = Path(state_dir)
        self.accounts_dir = self.state_dir / "accounts"
        self.accounts_dir.mkdir(parents=True, exist_ok=True)

    def _get_account_file(self, account_id: str) -> Path:
        """获取账号数据文件路径

        Args:
            account_id: 账号 ID

        Returns:
            文件路径
        """
        normalized_id = normalize_account_id(account_id)
        return self.accounts_dir / f"{normalized_id}.json"

    def save(
        self,
        account_id: str,
        token: str,
        base_url: str = "https://ilinkai.weixin.qq.com",
        user_id: Optional[str] = None,
    ) -> None:
        """保存 Token

        Args:
            account_id: 账号 ID
            token: Bot Token
            base_url: 基础 URL
            user_id: 用户 ID（可选）
        """
        normalized_id = normalize_account_id(account_id)
        file_path = self._get_account_file(normalized_id)

        # 读取现有数据（如果有）
        existing_data = {}
        if file_path.exists():
            try:
                with open(file_path, "r") as f:
                    existing_data = json.load(f)
            except Exception as e:
                logger.warning(f"读取现有 Token 数据失败: {e}")

        # 合并数据
        data = WeixinAccountData(
            token=token,
            saved_at=datetime.utcnow().isoformat(),
            base_url=base_url or existing_data.get("base_url", "https://ilinkai.weixin.qq.com"),
            user_id=user_id or existing_data.get("user_id"),
        ).model_dump(exclude_none=True)

        # 保存文件
        with open(file_path, "w") as f:
            json.dump(data, f, indent=2)

        # 设置权限（仅所有者可读写）
        os.chmod(file_path, 0o600)

        logger.info(f"Token 已保存: account_id={normalized_id}")

    def load(self, account_id: str) -> Optional[WeixinAccountData]:
        """加载 Token

        Args:
            account_id: 账号 ID

        Returns:
            Token 数据，不存在返回 None
        """
        normalized_id = normalize_account_id(account_id)
        file_path = self._get_account_file(normalized_id)

        if not file_path.exists():
            return None

        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            return WeixinAccountData(**data)

        except Exception as e:
            logger.error(f"加载 Token 失败: {e}")
            return None

    def delete(self, account_id: str) -> bool:
        """删除 Token

        Args:
            account_id: 账号 ID

        Returns:
            是否成功删除
        """
        normalized_id = normalize_account_id(account_id)
        file_path = self._get_account_file(normalized_id)

        if not file_path.exists():
            return False

        try:
            os.remove(file_path)
            logger.info(f"Token 已删除: account_id={normalized_id}")
            return True

        except Exception as e:
            logger.error(f"删除 Token 失败: {e}")
            return False

    def list_accounts(self) -> List[str]:
        """列出所有已保存的账号

        Returns:
            账号 ID 列表
        """
        accounts = []

        try:
            for file_path in self.accounts_dir.glob("*.json"):
                account_id = file_path.stem
                accounts.append(account_id)

        except Exception as e:
            logger.error(f"列出账号失败: {e}")

        return accounts

    def exists(self, account_id: str) -> bool:
        """检查 Token 是否存在

        Args:
            account_id: 账号 ID

        Returns:
            True 表示存在
        """
        normalized_id = normalize_account_id(account_id)
        file_path = self._get_account_file(normalized_id)
        return file_path.exists()

    def get_token(self, account_id: str) -> Optional[str]:
        """获取 Token（便捷方法）

        Args:
            account_id: 账号 ID

        Returns:
            Token，不存在返回 None
        """
        data = self.load(account_id)
        return data.token if data else None
