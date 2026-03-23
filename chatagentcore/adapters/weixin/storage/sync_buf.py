"""游标缓冲区存储

持久化长轮询游标，防止消息重复接收。
参考: openclaw-weixin/src/storage/sync-buf.ts
"""

import json
from pathlib import Path
from typing import Optional

from loguru import logger

from ..utils.helpers import normalize_account_id


# ---------------------------------------------------------------------------
# 游标缓冲区存储
# ---------------------------------------------------------------------------


class SyncBufStore:
    """游标缓冲区持久化存储

    将长轮询游标保存到文件系统，防止重启后消息重复接收。
    """

    def __init__(self, state_dir: Optional[str] = None):
        """初始化游标存储

        Args:
            state_dir: 状态目录，默认为 ~/.openclaw-weixin
        """
        if state_dir is None:
            home = Path.home()
            state_dir = home / ".openclaw-weixin"

        self.state_dir = Path(state_dir)
        self.sync_buf_dir = self.state_dir / "sync-buf"
        self.sync_buf_dir.mkdir(parents=True, exist_ok=True)

    def _get_sync_buf_file(self, account_id: str) -> Path:
        """获取游标文件路径

        Args:
            account_id: 账号 ID

        Returns:
            文件路径
        """
        normalized_id = normalize_account_id(account_id)
        return self.sync_buf_dir / f"{normalized_id}.json"

    def save(self, account_id: str, get_updates_buf: str) -> None:
        """保存游标

        Args:
            account_id: 账号 ID
            get_updates_buf: 游标缓冲区字符串
        """
        normalized_id = normalize_account_id(account_id)
        file_path = self._get_sync_buf_file(normalized_id)

        try:
            data = {
                "account_id": normalized_id,
                "get_updates_buf": get_updates_buf,
                "saved_at": self._get_current_timestamp(),
            }

            with open(file_path, "w") as f:
                json.dump(data, f, indent=2)

            logger.debug(f"游标已保存: account_id={normalized_id}, len={len(get_updates_buf)}")

        except Exception as e:
            logger.error(f"保存游标失败: {e}")

    def load(self, account_id: str) -> Optional[str]:
        """加载游标

        Args:
            account_id: 账号 ID

        Returns:
            游标字符串，不存在返回 None
        """
        normalized_id = normalize_account_id(account_id)
        file_path = self._get_sync_buf_file(normalized_id)

        if not file_path.exists():
            return None

        try:
            with open(file_path, "r") as f:
                data = json.load(f)

            return data.get("get_updates_buf")

        except Exception as e:
            logger.error(f"加载游标失败: {e}")
            return None

    def delete(self, account_id: str) -> bool:
        """删除游标

        Args:
            account_id: 账号 ID

        Returns:
            是否成功删除
        """
        normalized_id = normalize_account_id(account_id)
        file_path = self._get_sync_buf_file(normalized_id)

        if not file_path.exists():
            return False

        try:
            file_path.unlink()
            logger.debug(f"游标已删除: account_id={normalized_id}")
            return True

        except Exception as e:
            logger.error(f"删除游标失败: {e}")
            return False

    def _get_current_timestamp(self) -> str:
        """获取当前时间戳（ISO 8601）

        Returns:
            时间戳字符串
        """
        from datetime import datetime
        return datetime.utcnow().isoformat()
