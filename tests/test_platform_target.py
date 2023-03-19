from typing import Literal
from datetime import datetime

import pytest
from nonebug import App

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


async def test_export_args(app: App):
    from nonebot import get_driver
    from nonebot.adapters.onebot.v11 import Bot

    from nonebot_plugin_saa.utils import TargetQQGroup

    target = TargetQQGroup(group_id=31415)
    async with app.test_api() as ctx:
        ob11 = get_driver()._adapters[SupportedAdapters.onebot_v11]
        bot = ctx.create_bot(base=Bot, adapter=ob11)
        assert target.arg_dict(bot) == {"group_id": 31415, "message_type": "group"}


def test_extract_ob11(app: App):
    from nonebot.adapters.onebot.v11.event import Sender
    from nonebot.adapters.onebot.v11 import (
        Message,
        GroupMessageEvent,
        PrivateMessageEvent,
    )

    from nonebot_plugin_saa import TargetQQGroup, TargetQQPrivate, extract_target

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
    assert extract_target(group_message_event) == TargetQQGroup(group_id=1122)
    private_message_event = PrivateMessageEvent(
        time=1122,
        self_id=2233,
        post_type="message",
        sub_type="",
        user_id=3344,
        message_id=4455,
        message=Message("123"),
        original_message=Message("123"),
        message_type="private",
        raw_message="123",
        font=1,
        sender=sender,
    )
    assert extract_target(private_message_event) == TargetQQPrivate(user_id=3344)


def test_extract_ob12(app: App):
    from nonebot.adapters.onebot.v12.event import BotSelf
    from nonebot.adapters.onebot.v12 import (
        Message,
        GroupMessageEvent,
        ChannelMessageEvent,
        PrivateMessageEvent,
    )

    from nonebot_plugin_saa import TargetQQGroup, TargetQQPrivate, extract_target

    group_message_event = GroupMessageEvent(
        id="1122",
        time=datetime.now(),
        type="message",
        detail_type="group",
        sub_type="",
        message_id="2233",
        self=BotSelf(platform="qq", user_id="3344"),
        message=Message("123"),
        original_message=Message("123"),
        alt_message="123",
        user_id="3344",
        group_id="1122",
    )
    assert extract_target(group_message_event) == TargetQQGroup(group_id=1122)

    private_message_event = PrivateMessageEvent(
        id="1122",
        time=datetime.now(),
        type="message",
        detail_type="private",
        sub_type="",
        message_id="2233",
        self=BotSelf(platform="qq", user_id="3344"),
        message=Message("123"),
        original_message=Message("123"),
        alt_message="123",
        user_id="3344",
    )
    assert extract_target(private_message_event) == TargetQQPrivate(user_id=3344)

    channel_message_event = ChannelMessageEvent(
        id="1122",
        time=datetime.now(),
        type="message",
        detail_type="channel",
        sub_type="",
        message_id="2233",
        self=BotSelf(platform="qq", user_id="3344"),
        message=Message("123"),
        original_message=Message("123"),
        alt_message="123",
        user_id="3344",
        guild_id="5566",
        channel_id="6677",
    )
    with pytest.raises(RuntimeError):
        extract_target(channel_message_event)


def test_extract_qqguild(app: App):
    from nonebot.adapters.qqguild import EventType, MessageCreateEvent

    from nonebot_plugin_saa import TargetQQGuildChannel, extract_target

    group_message_event = MessageCreateEvent(
        __type__=EventType.CHANNEL_CREATE, channel_id=6677, guild_id=5566
    )
    assert extract_target(group_message_event) == TargetQQGuildChannel(channel_id=6677)


def test_unsupported_event(app: App):
    from nonebot.adapters.onebot.v11 import FriendRequestEvent

    from nonebot_plugin_saa import extract_target

    friend_req_event = FriendRequestEvent(
        time=1122,
        self_id=2233,
        post_type="request",
        request_type="friend",
        user_id=3344,
        comment="666",
        flag="123",
    )
    with pytest.raises(RuntimeError):
        extract_target(friend_req_event)


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
