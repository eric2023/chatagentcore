"""Unit tests for ConfigManager"""

import pytest
import tempfile
import yaml
from pathlib import Path
from chatagentcore.core.config_manager import ConfigManager


@pytest.fixture
def temp_config_file():
    """临时配置文件"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        config_path = Path(f.name)
        yaml.dump(
            {
                "server": {"host": "localhost", "port": 9000},
                "auth": {"type": "fixed_token", "token": "test_token"},
                "platforms": {
                    "feishu": {
                        "enabled": True,
                        "type": "app",
                        "config": {
                            "app_id": "test_app_id",
                            "app_secret": "test_secret",
                            "verification_token": "test_token",
                            "encrypt_key": "test_key",
                        },
                    }
                },
            },
            f,
        )
        yield config_path
    config_path.unlink(missing_ok=True)


def test_config_manager_load(temp_config_file: Path):
    """测试加载配置"""
    manager = ConfigManager(str(temp_config_file))
    config = manager.load()

    assert config.server.host == "localhost"
    assert config.server.port == 9000
    assert config.auth.type == "fixed_token"
    assert config.auth.token == "test_token"
    assert config.platforms.feishu.enabled is True
    assert config.platforms.feishu.config.app_id == "test_app_id"


def test_config_manager_version(temp_config_file: Path):
    """测试配置版本"""
    manager = ConfigManager(str(temp_config_file))

    config1 = manager.load()
    version1 = manager.version

    config2 = manager.reload()
    version2 = manager.version

    assert version2 == version1 + 1


def test_config_manager_to_dict(temp_config_file: Path):
    """测试配置转字典"""
    manager = ConfigManager(str(temp_config_file))
    config = manager.load()

    config_dict = manager.to_dict()

    assert "server" in config_dict
    assert "auth" in config_dict
    assert "platforms" in config_dict
    assert config_dict["server"]["host"] == "localhost"
