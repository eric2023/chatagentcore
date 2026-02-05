"""Message API routes"""

import time
from typing import Any, Dict
from fastapi import APIRouter, HTTPException, Depends, Header
from loguru import logger
from chatagentcore.api.models.message import (
    SendMessageRequest,
    SendMessageResponse,
    MessageStatusRequest,
    MessageStatusResponse,
    ConversationListRequest,
    ConversationListResponse,
    ConfigUpdateRequest,
    ConfigResponse,
)
from chatagentcore.core.adapter_manager import get_adapter_manager
from chatagentcore.core.router import get_router
from chatagentcore.core.config_manager import get_config_manager
from chatagentcore.core.event_bus import get_event_bus

router = APIRouter(prefix="/api/v1", tags=["message"])

# Token 验证依赖
async def verify_token(authorization: str = Header(None)) -> str:
    """验证 Token"""
    if not authorization:
        raise HTTPException(status_code=401, detail="Authorization header missing")

    token = authorization.replace("Bearer ", "") if authorization.startswith("Bearer ") else authorization

    # 简单验证（实际应该使用配置的 Token）
    config_manager = get_config_manager()
    valid_token = config_manager.config.auth.token

    if valid_token and token != valid_token:
        raise HTTPException(status_code=403, detail="Invalid token")

    return token


@router.post("/message/send", response_model=SendMessageResponse)
async def send_message(
    request: SendMessageRequest,
    token: str = Depends(verify_token),
) -> SendMessageResponse:
    """
    发送消息到聊天平台

    Args:
        request: 发送消息请求
        token: 认证 Token

    Returns:
        发送响应
    """
    # 打印发送的消息日志
    logger.info("=" * 70)
    logger.info("📤 发送消息 ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    logger.info(f"平台: {request.platform} | 类型: {request.message_type}")
    logger.info(f"接收者: {request.to} ({request.conversation_type})")
    logger.info("-" * 70)

    if request.message_type == "text":
        lines = request.content.split("\n") if "\n" in request.content else [request.content]
        for line in lines:
            logger.info(f"内容: {line}")
    elif request.message_type in ("card", "interactive"):
        logger.info(f"卡片消息: {request.content[:200]}...")
    else:
        logger.info(f"内容: {str(request.content)[:200]}")

    logger.info("=" * 70)

    router_instance = get_router()
    timestamp = int(time.time())

    try:
        message_id = await router_instance.route_outgoing(
            platform=request.platform,
            to=request.to,
            message_type=request.message_type,
            content=request.content,
            conversation_type=request.conversation_type,
        )

        logger.info(f"✅ 发送成功 | 消息 ID: {message_id}")

        # 发布消息事件
        event_bus = get_event_bus()
        await event_bus.emit("message:sent", {
            "platform": request.platform,
            "message_id": message_id,
            "to": request.to,
            "message_type": request.message_type,
        })

        return SendMessageResponse(
            code=0,
            message="success",
            data={"message_id": message_id, "status": "sent"},
            timestamp=timestamp,
        )
    except Exception as e:
        logger.error(f"❌ 发送失败: {e}")
        return SendMessageResponse(
            code=500,
            message=str(e),
            timestamp=timestamp,
        )


@router.post("/message/status", response_model=MessageStatusResponse)
async def get_message_status(
    request: MessageStatusRequest,
    token: str = Depends(verify_token),
) -> MessageStatusResponse:
    """
    查询消息状态

    Args:
        request: 查询请求
        token: 认证 Token

    Returns:
        消息状态响应
    """
    timestamp = int(time.time())

    # 暂时返回默认状态，实际需要根据平台实现
    return MessageStatusResponse(
        code=0,
        message="success",
        data={
            "platform": request.platform,
            "message_id": request.message_id,
            "status": "sent",  # sent | delivered | read | failed
            "sent_at": timestamp,
        },
        timestamp=timestamp,
    )


@router.post("/conversation/list", response_model=ConversationListResponse)
async def list_conversations(
    request: ConversationListRequest,
    token: str = Depends(verify_token),
) -> ConversationListResponse:
    """
    获取会话列表

    Args:
        request: 查询请求
        token: 认证 Token

    Returns:
        会话列表响应
    """
    timestamp = int(time.time())

    # 暂时返回空列表，实际需要根据平台实现
    return ConversationListResponse(
        code=0,
        message="success",
        data={
            "conversations": [],
            "has_more": False,
            "cursor": None,
        },
        timestamp=timestamp,
    )


@router.get("/config", response_model=ConfigResponse)
async def get_config(token: str = Depends(verify_token)) -> ConfigResponse:
    """
    获取配置信息

    Args:
        token: 认证 Token

    Returns:
        配置响应
    """
    config_manager = get_config_manager()
    timestamp = int(time.time())

    # 只返回非敏感配置
    config_data = {
        "server": config_manager.config.server.model_dump(),
        "platforms": {
            platform: {"enabled": cfg.enabled, "type": cfg.type}
            for platform, cfg in [
                ("feishu", config_manager.platforms.feishu),
                ("wecom", config_manager.platforms.wecom),
                ("dingtalk", config_manager.platforms.dingtalk),
            ]
        },
        "logging": {
            "level": config_manager.config.logging.level,
            "file": config_manager.config.logging.file,
        },
    }

    return ConfigResponse(
        code=0,
        message="success",
        data=config_data,
        timestamp=timestamp,
    )


@router.post("/config", response_model=ConfigResponse)
async def update_config(
    request: ConfigUpdateRequest,
    token: str = Depends(verify_token),
) -> ConfigResponse:
    """
    更新平台配置

    Args:
        request: 更新请求
        token: 认证 Token

    Returns:
        配置响应
    """
    config_manager = get_config_manager()
    timestamp = int(time.time())

    try:
        platforms = {
            "feishu": config_manager.platforms.feishu,
            "wecom": config_manager.platforms.wecom,
            "dingtalk": config_manager.platforms.dingtalk,
        }

        if request.platform not in platforms:
            raise HTTPException(status_code=400, detail=f"Invalid platform: {request.platform}")

        platform_config = platforms[request.platform]

        # 更新配置
        if request.enabled is not None:
            platform_config.enabled = request.enabled

        result = {
            "platform": request.platform,
            "enabled": platform_config.enabled,
            "status": "active" if platform_config.enabled else "inactive",
        }

        return ConfigResponse(
            code=0,
            message="success",
            data=result,
            timestamp=timestamp,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating config: {e}")
        return ConfigResponse(
            code=500,
            message=str(e),
            timestamp=timestamp,
        )


__all__ = ["router"]
