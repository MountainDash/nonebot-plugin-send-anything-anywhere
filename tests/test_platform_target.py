from typing import Literal

import pytest
from nonebug import App
from pydantic import BaseModel

from nonebot_plugin_saa.utils.const import SupportedAdapters


def test_register_deserializer():
    from nonebot_plugin_saa.utils import SupportedPlatform
    from nonebot_plugin_saa.utils.platform_send_target import PlatformTarget

    class MySendTarget(PlatformTarget):
        platform_type: Literal[SupportedPlatform.qq_group] = SupportedPlatform.qq_group
        my_field: int

    send_target = MySendTarget(my_field=123)
    serialized_target = send_target.json()
    deserialized_target = PlatformTarget.deserialize(serialized_target)

    assert isinstance(deserialized_target, MySendTarget)
    assert deserialized_target == send_target

    serialized_target = send_target.dict()
    deserialized_target = PlatformTarget.deserialize(serialized_target)

    assert isinstance(deserialized_target, MySendTarget)
    assert deserialized_target == send_target


def test_deserialize_nested_platform_target():
    from nonebot_plugin_saa.utils import (
        TargetQQGroup,
        TargetQQPrivate,
        AllSupportedPlatformTarget,
    )

    class CustomModel(BaseModel):
        data: AllSupportedPlatformTarget

    model = CustomModel(data=TargetQQGroup(group_id=123))
    serialized_model = model.dict()
    deserialized_model = CustomModel.parse_obj(serialized_model)
    assert model == deserialized_model

    model = CustomModel(data=TargetQQPrivate(user_id=456))
    serialized_model = model.dict()
    deserialized_model = CustomModel.parse_obj(serialized_model)
    assert model == deserialized_model


async def test_export_args(app: App):
    from nonebot import get_driver
    from nonebot.adapters.onebot.v11 import Bot

    from nonebot_plugin_saa.utils import TargetQQGroup

    target = TargetQQGroup(group_id=31415)
    async with app.test_api() as ctx:
        ob11 = get_driver()._adapters[SupportedAdapters.onebot_v11]
        bot = ctx.create_bot(base=Bot, adapter=ob11)
        assert target.arg_dict(bot) == {"group_id": 31415, "message_type": "group"}


def test_unsupported_event(app: App):
    from nonebot.adapters.onebot.v11.event import Status
    from nonebot.adapters.onebot.v11 import HeartbeatMetaEvent

    from nonebot_plugin_saa import extract_target

    heartbeat_meta_event = HeartbeatMetaEvent(
        time=1122,
        self_id=2233,
        post_type="meta_event",
        meta_event_type="heartbeat",
        status=Status(online=True, good=True),
        interval=10,
    )
    with pytest.raises(RuntimeError):
        extract_target(heartbeat_meta_event)


async def test_unable_to_convert(app: App):
    from nonebot import get_driver
    from nonebot.adapters.onebot.v11 import Bot

    from nonebot_plugin_saa import SupportedAdapters, TargetQQGuildChannel

    target = TargetQQGuildChannel(channel_id=1122)
    async with app.test_api() as ctx:
        adapter_ob11 = get_driver()._adapters[str(SupportedAdapters.onebot_v11)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_ob11)
        with pytest.raises(RuntimeError):
            target.arg_dict(bot)


def test_get_target(app: App):
    from nonebot.adapters.onebot.v11.event import Sender, Status
    from nonebot.adapters.onebot.v11 import (
        Message,
        GroupMessageEvent,
        HeartbeatMetaEvent,
    )

    from nonebot_plugin_saa import TargetQQGroup, get_target

    sender = Sender(user_id=3344)
    group_message_event = GroupMessageEvent(
        group_id=1122,
        time=1122,
        self_id=2233,
        post_type="message",
        sub_type="",
        user_id=3344,
        message_id=4455,
        message=Message("123"),
        original_message=Message("123"),
        message_type="group",
        raw_message="123",
        font=1,
        sender=sender,
    )
    assert get_target(group_message_event) == TargetQQGroup(group_id=1122)

    heartbeat_meta_event = HeartbeatMetaEvent(
        time=1122,
        self_id=2233,
        post_type="meta_event",
        meta_event_type="heartbeat",
        status=Status(online=True, good=True),
        interval=10,
    )
    assert get_target(heartbeat_meta_event) is None
