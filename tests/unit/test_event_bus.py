"""Unit tests for EventBus"""

import pytest
import asyncio
from chatagentcore.core.event_bus import EventBus


@pytest.mark.asyncio
async def test_event_bus_publish_and_subscribe():
    """测试事件发布和订阅"""
    bus = EventBus()
    await bus.start()

    # 订阅频道
    channel = "test:channel"
    queue = await bus.subscribe(channel)

    # 发布事件
    test_event = {"data": "test"}
    await bus.publish(channel, test_event)

    # 接收事件
    result = await asyncio.wait_for(queue.get(), timeout=1.0)

    assert result["event"] == test_event
    assert result["channel"] == channel

    await bus.stop()


@pytest.mark.asyncio
async def test_event_bus_multiple_subscribers():
    """测试多个订阅者"""
    bus = EventBus()
    await bus.start()

    channel = "test:multi"
    queue1 = await bus.subscribe(channel)
    queue2 = await bus.subscribe(channel)

    test_event = {"data": "multi"}
    await bus.publish(channel, test_event)

    # 两个订阅者都应该收到
    result1 = await asyncio.wait_for(queue1.get(), timeout=1.0)
    result2 = await asyncio.wait_for(queue2.get(), timeout=1.0)

    assert result1["event"] == test_event
    assert result2["event"] == test_event

    await bus.stop()


@pytest.mark.asyncio
async def test_event_bus_wildcard():
    """测试通配符订阅"""
    bus = EventBus()
    await bus.start()

    # 订阅所有 test:* 消息
    queue = await bus.subscribe("test:*")

    # 发布到 test:channel1
    await bus.publish("test:channel1", {"data": "wildcard1"})

    result = await asyncio.wait_for(queue.get(), timeout=1.0)
    assert result["channel"] == "test:channel1"

    # 发布到 test:channel2
    await bus.publish("test:channel2", {"data": "wildcard2"})

    result = await asyncio.wait_for(queue.get(), timeout=1.0)
    assert result["channel"] == "test:channel2"

    # 发布到 other:channel（不应该收到）
    await bus.publish("other:channel", {"data": "other"})

    # 队列应该为空
    assert queue.empty()

    await bus.stop()


@pytest.mark.asyncio
async def test_event_bus_handler():
    """测试事件处理器"""
    bus = EventBus()
    await bus.start()

    received_events = []

    def handler(event):
        received_events.append(event)

    bus.on("test:handler", handler)
    await bus.emit("test:handler", {"data": "handler"})

    assert len(received_events) == 1
    assert received_events[0] == {"data": "handler"}

    await bus.stop()


@pytest.mark.asyncio
async def test_event_bus_unsubscribe():
    """测试取消订阅"""
    bus = EventBus()
    await bus.start()

    channel = "test:unsubscribe"
    queue = await bus.subscribe(channel)

    # 取消订阅
    await bus.unsubscribe(channel, queue)

    # 发布事件后队列应该为空
    await bus.publish(channel, {"data": "after unsubscribe"})
    assert queue.empty()

    await bus.stop()
