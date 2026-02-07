from fastapi import APIRouter, HTTPException, Depends
from typing import Dict, Any
from loguru import logger
from chatagentcore.core.config_manager import get_config_manager
from chatagentcore.api.schemas.config import Settings
import yaml
from pathlib import Path

router = APIRouter(prefix="/api/config", tags=["config"])

@router.get("")
async def get_current_config():
    """获取当前所有配置项"""
    config_manager = get_config_manager()
    # 转换为字典并返回，隐藏敏感信息可以在前端处理或此处处理
    return config_manager.to_dict()

@router.post("/update")
async def update_config(new_config: Dict[str, Any]):
    """更新并保存配置文件"""
    config_manager = get_config_manager()
    config_path = config_manager.config_path
    import copy
    
    try:
        # 1. 验证新配置
        # 使用 deepcopy 避免原地修改内存中的当前配置，确保 reload 能够检测到差异
        current_raw = copy.deepcopy(config_manager._raw_config)
        
        # 深度合并或简单更新顶级 key
        for key, value in new_config.items():
            if key in current_raw and isinstance(current_raw[key], dict) and isinstance(value, dict):
                current_raw[key].update(value)
            else:
                current_raw[key] = value
        
        # 验证完整性
        Settings.model_validate(current_raw)
        
        # 2. 写入文件
        with open(config_path, "w", encoding="utf-8") as f:
            yaml.dump(current_raw, f, allow_unicode=True, sort_keys=False)
        
        # 3. 不再手动调用 reload()，交给 watch_loop 自动感应文件变化
        # 这可以防止 Web 保存和文件监控同时触发导致的双重重载
        
        logger.info(f"配置已通过 Web 后台更新并保存至 {config_path}，等待自动重载生效")
        return {"status": "success", "message": "配置已保存，系统将在几秒内自动生效"}
        
    except Exception as e:
        logger.error(f"更新配置失败: {e}")
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/status")
async def get_system_status():
    """获取系统运行状态（含 Agent 状态）"""
    from chatagentcore.core.process_manager import get_process_manager
    from chatagentcore.core.adapter_manager import get_adapter_manager
    
    pm = get_process_manager()
    am = get_adapter_manager()
    
    return {
        "agent": {
            "name": "uos-ai-assistant",
            "running": pm.process is not None and pm.process.returncode is None,
            "pid": pm.process.pid if pm.process else None
        },
        "platforms": {
            name: {
                "enabled": adapter.is_connected() if hasattr(adapter, 'is_connected') else True,
                "type": name
            } for name, adapter in am._adapters.items()
        }
    }
