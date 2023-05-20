from typing import Literal
from datetime import datetime

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


def test_extract_ob11(app: App):
    from nonebot.adapters.onebot.v11.event import File, Sender
    from nonebot.adapters.onebot.v11 import (
        Message,
        PokeNotifyEvent,
        HonorNotifyEvent,
        GroupMessageEvent,
        GroupRequestEvent,
        FriendRequestEvent,
        GroupBanNoticeEvent,
        PrivateMessageEvent,
        FriendAddNoticeEvent,
        LuckyKingNotifyEvent,
        GroupAdminNoticeEvent,
        GroupRecallNoticeEvent,
        GroupUploadNoticeEvent,
        FriendRecallNoticeEvent,
        GroupDecreaseNoticeEvent,
        GroupIncreaseNoticeEvent,
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

    friend_add_notice_event = FriendAddNoticeEvent(
        time=1122,
        self_id=2233,
        post_type="notice",
        notice_type="friend_add",
        user_id=3344,
    )
    assert extract_target(friend_add_notice_event) == TargetQQPrivate(user_id=3344)

    friend_recall_notice_event = FriendRecallNoticeEvent(
        time=1122,
        self_id=2233,
        post_type="notice",
        notice_type="friend_recall",
        user_id=3344,
        message_id=4455,
    )
    assert extract_target(friend_recall_notice_event) == TargetQQPrivate(user_id=3344)

    group_ban_notice_event = GroupBanNoticeEvent(
        time=1122,
        self_id=2233,
        post_type="notice",
        notice_type="group_ban",
        sub_type="",
        group_id=1122,
        operator_id=3344,
        user_id=5566,
        duration=10,
    )
    assert extract_target(group_ban_notice_event) == TargetQQGroup(group_id=1122)

    group_recall_notice_event = GroupRecallNoticeEvent(
        time=1122,
        self_id=2233,
        post_type="notice",
        notice_type="group_recall",
        group_id=1122,
        operator_id=3344,
        user_id=5566,
        message_id=4455,
    )
    assert extract_target(group_recall_notice_event) == TargetQQGroup(group_id=1122)

    group_admin_notice_event = GroupAdminNoticeEvent(
        time=1122,
        self_id=2233,
        post_type="notice",
        notice_type="group_admin",
        sub_type="",
        group_id=1122,
        user_id=5566,
    )
    assert extract_target(group_admin_notice_event) == TargetQQGroup(group_id=1122)

    group_decrease_notice_event = GroupDecreaseNoticeEvent(
        time=1122,
        self_id=2233,
        post_type="notice",
        notice_type="group_decrease",
        sub_type="",
        group_id=1122,
        operator_id=3344,
        user_id=5566,
    )
    assert extract_target(group_decrease_notice_event) == TargetQQGroup(group_id=1122)

    group_increase_notice_event = GroupIncreaseNoticeEvent(
        time=1122,
        self_id=2233,
        post_type="notice",
        notice_type="group_increase",
        sub_type="",
        group_id=1122,
        operator_id=3344,
        user_id=5566,
    )
    assert extract_target(group_increase_notice_event) == TargetQQGroup(group_id=1122)

    group_upload_notice_event = GroupUploadNoticeEvent(
        time=1122,
        self_id=2233,
        post_type="notice",
        notice_type="group_upload",
        group_id=1122,
        user_id=3344,
        file=File(id="4455", name="123", size=10, busid=6677),
    )
    assert extract_target(group_upload_notice_event) == TargetQQGroup(group_id=1122)

    honor_notify_event = HonorNotifyEvent(
        time=1122,
        self_id=2233,
        post_type="notice",
        notice_type="notify",
        sub_type="honor",
        group_id=1122,
        user_id=3344,
        honor_type="talkative",
    )
    assert extract_target(honor_notify_event) == TargetQQGroup(group_id=1122)

    lucky_king_notify_event = LuckyKingNotifyEvent(
        time=1122,
        self_id=2233,
        post_type="notice",
        notice_type="notify",
        sub_type="lucky_king",
        group_id=1122,
        user_id=3344,
        target_id=5566,
    )
    assert extract_target(lucky_king_notify_event) == TargetQQGroup(group_id=1122)

    friend_request_event = FriendRequestEvent(
        time=1122,
        self_id=2233,
        post_type="request",
        request_type="friend",
        user_id=3344,
        comment="123",
        flag="2233",
    )
    assert extract_target(friend_request_event) == TargetQQPrivate(user_id=3344)

    group_request_event = GroupRequestEvent(
        time=1122,
        self_id=2233,
        post_type="request",
        request_type="group",
        sub_type="",
        group_id=1122,
        user_id=3344,
        comment="123",
        flag="2233",
    )
    assert extract_target(group_request_event) == TargetQQGroup(group_id=1122)

    poke_notify_event = PokeNotifyEvent(
        time=1122,
        self_id=2233,
        post_type="notice",
        notice_type="notify",
        sub_type="poke",
        group_id=1122,
        user_id=3344,
        target_id=5566,
    )
    assert extract_target(poke_notify_event) == TargetQQGroup(group_id=1122)

    poke_notify_event = PokeNotifyEvent(
        time=1122,
        self_id=2233,
        post_type="notice",
        notice_type="notify",
        sub_type="poke",
        group_id=None,
        user_id=3344,
        target_id=5566,
    )
    assert extract_target(poke_notify_event) == TargetQQPrivate(user_id=3344)


def test_extract_ob12(app: App):
    from nonebot.adapters.onebot.v12.event import BotSelf
    from nonebot.adapters.onebot.v12 import (
        Message,
        GroupMessageEvent,
        ChannelMessageEvent,
        FriendDecreaseEvent,
        FriendIncreaseEvent,
        PrivateMessageEvent,
        GroupMessageDeleteEvent,
        GroupMemberDecreaseEvent,
        GroupMemberIncreaseEvent,
        PrivateMessageDeleteEvent,
    )

    from nonebot_plugin_saa import (
        TargetQQGroup,
        TargetQQPrivate,
        TargetOB12Unknow,
        TargetQQGuildDirect,
        TargetQQGuildChannel,
        extract_target,
    )

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

    assert extract_target(channel_message_event) == TargetOB12Unknow(
        detail_type="channel", guild_id="5566", channel_id="6677"
    )

    qqguild_private_message_event = PrivateMessageEvent(
        id="1122",
        time=datetime.now(),
        type="message",
        detail_type="private",
        sub_type="",
        message_id="2233",
        self=BotSelf(platform="qqguild", user_id="3344"),
        message=Message("123"),
        original_message=Message("123"),
        alt_message="123",
        user_id="3344",
        qqguild={
            "guild_id": "4455",
            "src_guild_id": "5566",
        },
    )
    assert extract_target(qqguild_private_message_event) == TargetQQGuildDirect(
        recipient_id=3344, source_guild_id=5566
    )

    qqguild_channel_message_event = ChannelMessageEvent(
        id="1122",
        time=datetime.now(),
        type="message",
        detail_type="channel",
        sub_type="",
        message_id="2233",
        self=BotSelf(platform="qqguild", user_id="3344"),
        message=Message("123"),
        original_message=Message("123"),
        alt_message="123",
        user_id="3344",
        guild_id="5566",
        channel_id="6677",
    )

    assert extract_target(qqguild_channel_message_event) == TargetQQGuildChannel(
        channel_id=6677
    )

    friend_decrease_event = FriendDecreaseEvent(
        id="1122",
        time=datetime.now(),
        type="notice",
        detail_type="friend_decrease",
        sub_type="",
        self=BotSelf(platform="qq", user_id="3344"),
        user_id="5566",
    )
    assert extract_target(friend_decrease_event) == TargetQQPrivate(user_id=5566)

    friend_decrease_event = FriendDecreaseEvent(
        id="1122",
        time=datetime.now(),
        type="notice",
        detail_type="friend_decrease",
        sub_type="",
        self=BotSelf(platform="wechat", user_id="3344"),
        user_id="5566",
    )
    assert extract_target(friend_decrease_event) == TargetOB12Unknow(
        detail_type="private", user_id="5566"
    )

    friend_increase_event = FriendIncreaseEvent(
        id="1122",
        time=datetime.now(),
        type="notice",
        detail_type="friend_increase",
        sub_type="",
        self=BotSelf(platform="qq", user_id="3344"),
        user_id="5566",
    )
    assert extract_target(friend_increase_event) == TargetQQPrivate(user_id=5566)

    friend_increase_event = FriendIncreaseEvent(
        id="1122",
        time=datetime.now(),
        type="notice",
        detail_type="friend_increase",
        sub_type="",
        self=BotSelf(platform="wechat", user_id="3344"),
        user_id="5566",
    )
    assert extract_target(friend_increase_event) == TargetOB12Unknow(
        detail_type="private", user_id="5566"
    )

    private_message_delete_event = PrivateMessageDeleteEvent(
        id="1122",
        time=datetime.now(),
        type="notice",
        detail_type="private_message_delete",
        sub_type="",
        self=BotSelf(platform="qq", user_id="3344"),
        user_id="5566",
        message_id="6677",
    )
    assert extract_target(private_message_delete_event) == TargetQQPrivate(user_id=5566)

    private_message_delete_event = PrivateMessageDeleteEvent(
        id="1122",
        time=datetime.now(),
        type="notice",
        detail_type="private_message_delete",
        sub_type="",
        self=BotSelf(platform="wechat", user_id="3344"),
        user_id="5566",
        message_id="6677",
    )
    assert extract_target(private_message_delete_event) == TargetOB12Unknow(
        detail_type="private", user_id="5566"
    )

    group_message_delete_event = GroupMessageDeleteEvent(
        id="1122",
        time=datetime.now(),
        type="notice",
        detail_type="group_message_delete",
        sub_type="",
        self=BotSelf(platform="qq", user_id="3344"),
        user_id="5566",
        group_id="6677",
        message_id="7788",
        operator_id="8899",
    )
    assert extract_target(group_message_delete_event) == TargetQQGroup(group_id=6677)

    group_message_delete_event = GroupMessageDeleteEvent(
        id="1122",
        time=datetime.now(),
        type="notice",
        detail_type="group_message_delete",
        sub_type="",
        self=BotSelf(platform="wechat", user_id="3344"),
        user_id="5566",
        group_id="6677",
        message_id="7788",
        operator_id="8899",
    )
    assert extract_target(group_message_delete_event) == TargetOB12Unknow(
        detail_type="group", group_id="6677"
    )

    group_member_decrease_event = GroupMemberDecreaseEvent(
        id="1122",
        time=datetime.now(),
        type="notice",
        detail_type="group_member_decrease",
        sub_type="",
        self=BotSelf(platform="qq", user_id="3344"),
        user_id="5566",
        group_id="6677",
        operator_id="7788",
    )
    assert extract_target(group_member_decrease_event) == TargetQQGroup(group_id=6677)

    group_member_decrease_event = GroupMemberDecreaseEvent(
        id="1122",
        time=datetime.now(),
        type="notice",
        detail_type="group_member_decrease",
        sub_type="",
        self=BotSelf(platform="wechat", user_id="3344"),
        user_id="5566",
        group_id="6677",
        operator_id="7788",
    )
    assert extract_target(group_member_decrease_event) == TargetOB12Unknow(
        detail_type="group", group_id="6677"
    )

    group_member_increase_event = GroupMemberIncreaseEvent(
        id="1122",
        time=datetime.now(),
        type="notice",
        detail_type="group_member_increase",
        sub_type="",
        self=BotSelf(platform="qq", user_id="3344"),
        user_id="5566",
        group_id="6677",
        operator_id="7788",
    )
    assert extract_target(group_member_increase_event) == TargetQQGroup(group_id=6677)

    group_member_increase_event = GroupMemberIncreaseEvent(
        id="1122",
        time=datetime.now(),
        type="notice",
        detail_type="group_member_increase",
        sub_type="",
        self=BotSelf(platform="wechat", user_id="3344"),
        user_id="5566",
        group_id="6677",
        operator_id="7788",
    )
    assert extract_target(group_member_increase_event) == TargetOB12Unknow(
        detail_type="group", group_id="6677"
    )


def test_extract_qqguild(app: App):
    from nonebot.adapters.qqguild import EventType, MessageCreateEvent

    from nonebot_plugin_saa import TargetQQGuildChannel, extract_target

    group_message_event = MessageCreateEvent(
        __type__=EventType.CHANNEL_CREATE, channel_id=6677, guild_id=5566
    )
    assert extract_target(group_message_event) == TargetQQGuildChannel(channel_id=6677)


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
