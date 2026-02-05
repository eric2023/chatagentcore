"""Test configuration"""

import pytest
from pathlib import Path


@pytest.fixture
def project_root() -> Path:
    """项目根目录"""
    return Path(__file__).parent.parent.parent


@pytest.fixture
def test_data_dir(project_root: Path) -> Path:
    """测试数据目录"""
    data_dir = project_root / "tests" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir
