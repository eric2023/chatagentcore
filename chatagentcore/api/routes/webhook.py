"""Webhook 路由 - 处理平台回调消息"""

import json
from typing import Dict, Any
from fastapi import APIRouter, Header, Request, HTTPException
from loguru import logger

from chatagentcore.core.adapter_manager import get_adapter_manager
from chatagentcore.core.config_manager import get_config_manager

router = APIRouter(prefix="/webhook", tags=["webhook"])

# 全局事件处理器映射
_event_handlers: Dict[str, Dict[str, Any]] = {}


def register_event_handler(platform: str, handler: Any):
    """注册平台事件处理器"""
    if platform not in _event_handlers:
        _event_handlers[platform] = {}
    _event_handlers[platform] = handler
    logger.info(f"Registered webhook handler for platform: {platform}")


def unregister_event_handler(platform: str):
    """注销平台事件处理器"""
    if platform in _event_handlers:
        del _event_handlers[platform]
        logger.info(f"Unregistered webhook handler for platform: {platform}")


def get_event_handler(platform: str) -> Any:
    """获取平台事件处理器"""
    return _event_handlers.get(platform)


@router.post("/feishu")
async def feishu_webhook(
    request: Request,
    x_lark_request_timestamp: str = Header(None),
    x_lark_request_nonce: str = Header(None),
    x_lark_signature: str = Header(None),
):
    """
    处理飞书 Webhook 回调

    飞书开放平台会通过 HTTP POST 向此端点推送消息事件。
    """
    try:
        body = await request.body()

        logger.debug(f"收到飞书 Webhook 请求: {body.decode('utf-8', errors='ignore')}")

        # 解析 JSON
        event_data = json.loads(body)

        # 检查是否是 URL 验证请求
        if event_data.get("type") == "url_verification":
            challenge = event_data.get("challenge", "")
            logger.info(f"飞书 URL 验证请求，返回 challenge: {challenge}")
            return {"challenge": challenge}

        # 处理消息事件
        event_type = event_data.get("header", {}).get("event_type", "")
        logger.info(f"收到飞书事件: {event_type}")

        # 调用处理器（如果已注册）
        handler = get_event_handler("feishu")
        if handler:
            if hasattr(handler, "handle_webhook"):
                result = handler.handle_webhook(event_data)
                if result:
                    return result
            elif callable(handler):
                result = handler(event_data)
                if result:
                    return result

        # 简单响应
        return {"msg": "success"}

    except json.JSONDecodeError as e:
        logger.error(f"飞书 Webhook JSON 解析失败: {e}")
        raise HTTPException(status_code=400, detail="Invalid JSON")

    except Exception as e:
        logger.error(f"飞书 Webhook 处理异常: {e}")
        raise HTTPException(status_code=500, detail=f"Webhook 处理失败: {str(e)}")


@router.post("/wecom")
async def wecom_webhook(request: Request):
    """处理企业微信 Webhook 回调"""
    try:
        body = await request.body()
        event_data = xml.etree.ElementTree.fromstring(body.decode('utf-8'))

        msg_type = event_data.findtext("MsgType")
        logger.info(f"收到企业微信事件: {msg_type}")

        handler = get_event_handler("wecom")
        if handler:
            result = handler(event_data)
            if result:
                return result

        return {"errcode": 0, "errmsg": "success"}

    except Exception as e:
        logger.error(f"企业微信 Webhook 处理异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dingtalk")
async def dingtalk_webhook(request: Request):
    """处理钉钉 Webhook 回调"""
    try:
        body = await request.body()
        event_data = json.loads(body)

        msg_type = event_data.get("msgType")
        logger.info(f"收到钉钉事件: {msg_type}")

        handler = get_event_handler("dingtalk")
        if handler:
            result = handler(event_data)
            if result:
                return result

        return {"errcode": 0, "errmsg": "success"}

    except Exception as e:
        logger.error(f"钉钉 Webhook 处理异常: {e}")
        raise HTTPException(status_code=500, detail=str(e))


__all__ = [
    "router",
    "register_event_handler",
    "unregister_event_handler",
    "get_event_handler",
]
