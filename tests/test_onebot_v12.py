from io import BytesIO
from pathlib import Path
from datetime import datetime
from functools import partial

import pytest
from nonebug import App
from pytest_mock import MockerFixture
from nonebot import get_driver, get_adapter
from nonebot.adapters.onebot.v12 import Bot, Adapter, Message, MessageSegment

from .utils import assert_ms, ob12_kwargs, mock_obv12_message_event


@pytest.fixture
def assert_onebot_v12(app: App):
    from nonebot_plugin_saa import SupportedAdapters

    return partial(
        assert_ms, Bot, SupportedAdapters.onebot_v12, self_id="314159", **ob12_kwargs()
    )


async def test_text(app: App, assert_onebot_v12):
    from nonebot_plugin_saa import Text

    await assert_onebot_v12(app, Text("123"), MessageSegment.text("123"))


async def test_image(app: App):
    from nonebot_plugin_saa import Image, SupportedAdapters

    adapter = get_driver()._adapters[str(SupportedAdapters.onebot_v12)]

    async with app.test_api() as ctx:
        bot = ctx.create_bot(
            base=Bot, adapter=adapter, self_id="314159", **ob12_kwargs()
        )
        ctx.should_call_api(
            "upload_file",
            {"type": "url", "name": "image", "url": "https://example.com/image.png"},
            {"file_id": "123"},
        )
        generated_ms = await Image("https://example.com/image.png").build(bot)
        assert generated_ms == MessageSegment.image("123")

    async with app.test_api() as ctx:
        bot = ctx.create_bot(
            base=Bot, adapter=adapter, self_id="314159", **ob12_kwargs()
        )

        data = b"\x89PNG\r"

        ctx.should_call_api(
            "upload_file",
            {"type": "data", "name": "image", "data": data},
            {"file_id": "123"},
        )
        generated_ms = await Image(data).build(bot)
        assert generated_ms == MessageSegment.image("123")

    async with app.test_api() as ctx:
        bot = ctx.create_bot(
            base=Bot, adapter=adapter, self_id="314159", **ob12_kwargs()
        )

        image_path = Path(__file__).parent / "image.png"

        ctx.should_call_api(
            "upload_file",
            {"type": "path", "name": "image", "path": str(image_path.resolve())},
            {"file_id": "123"},
        )
        generated_ms = await Image(image_path).build(bot)
        assert generated_ms == MessageSegment.image("123")

    async with app.test_api() as ctx:
        bot = ctx.create_bot(
            base=Bot, adapter=adapter, self_id="314159", **ob12_kwargs()
        )

        data = BytesIO(b"\x89PNG\r")

        ctx.should_call_api(
            "upload_file",
            {"type": "data", "name": "image", "data": b"\x89PNG\r"},
            {"file_id": "123"},
        )
        generated_ms = await Image(data).build(bot)
        assert generated_ms == MessageSegment.image("123")


async def test_mention(app: App, assert_onebot_v12):
    from nonebot.adapters.onebot.v12 import MessageSegment

    from nonebot_plugin_saa import Mention

    await assert_onebot_v12(app, Mention("123"), MessageSegment.mention("123"))


async def test_mention_all(app: App, assert_onebot_v12):
    from nonebot.adapters.onebot.v12 import MessageSegment

    from nonebot_plugin_saa import MentionAll

    await assert_onebot_v12(app, MentionAll(), MessageSegment.mention_all())


async def test_reply(app: App, assert_onebot_v12):
    from nonebot.adapters.onebot.v12 import MessageSegment

    from nonebot_plugin_saa import Reply
    from nonebot_plugin_saa.adapters.onebot_v12 import OB12MessageId

    await assert_onebot_v12(
        app, Reply(OB12MessageId(message_id="123")), MessageSegment.reply("123")
    )


async def test_send_revoke(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.onebot.v12 import Bot, Message

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters

    matcher = on_message()

    @matcher.handle()
    async def handle():
        receipt = await MessageFactory(Text("123")).send()
        await receipt.revoke()

    async with app.test_matcher(matcher) as ctx:
        ob12_adapter = get_driver()._adapters[str(SupportedAdapters.onebot_v12)]
        bot = ctx.create_bot(base=Bot, adapter=ob12_adapter, **ob12_kwargs())
        message = Message("321")
        message_event = mock_obv12_message_event(message)

        ctx.receive_event(bot, message_event)
        ctx.should_call_api(
            "send_message",
            data={
                "message": Message("123"),
                "detail_type": "private",
                "user_id": message_event.user_id,
            },
            result={"message_id": "12355223"},
        )

        ctx.should_call_api("delete_message", {"message_id": "12355223"})


async def test_send(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.onebot.v12 import Bot, Message

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters

    matcher = on_message()

    @matcher.handle()
    async def handle():
        await MessageFactory(Text("123")).send()

    async with app.test_matcher(matcher) as ctx:
        ob12_adapter = get_driver()._adapters[str(SupportedAdapters.onebot_v12)]
        bot = ctx.create_bot(base=Bot, adapter=ob12_adapter, **ob12_kwargs())
        message = Message("321")
        message_event = mock_obv12_message_event(message)

        ctx.receive_event(bot, message_event)
        ctx.should_call_api(
            "send_message",
            data={
                "message": Message("123"),
                "detail_type": "private",
                "user_id": message_event.user_id,
            },
            result={"message_id": "12355223"},
        )

    async with app.test_matcher(matcher) as ctx:
        bot = ctx.create_bot(
            base=Bot, adapter=ob12_adapter, **ob12_kwargs(platform="qqguild")
        )
        message = Message("321")
        message_event = mock_obv12_message_event(message, detail_type="qqguild_private")
        ctx.receive_event(bot, message_event)
        ctx.should_call_api(
            "create_dms",
            data={
                "user_id": "2233",
                "src_guild_id": "5566",
            },
            result={"guild_id": "3333"},
        )
        ctx.should_call_api(
            "send_message",
            data={
                "message": Message("123"),
                "detail_type": "private",
                "guild_id": "3333",
                "event_id": "1111",
            },
            result={"message_id": "12355223"},
        )

        message_event = mock_obv12_message_event(message, detail_type="qqguild_channel")
        ctx.receive_event(bot, message_event)
        ctx.should_call_api(
            "send_message",
            data={
                "message": Message("123"),
                "detail_type": "channel",
                "channel_id": "6677",
                "event_id": "1111",
            },
            result={"message_id": "12355223"},
        )


async def test_extract_message_id(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.onebot.v12 import Bot, Message

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters
    from nonebot_plugin_saa.adapters.onebot_v12 import OB12Receipt, OB12MessageId

    matcher = on_message()

    @matcher.handle()
    async def handle():
        receipt = await MessageFactory(Text("123")).send()
        assert isinstance(receipt, OB12Receipt)
        assert receipt.extract_message_id() == OB12MessageId(message_id="12355223")

    async with app.test_matcher(matcher) as ctx:
        ob12_adapter = get_driver()._adapters[str(SupportedAdapters.onebot_v12)]
        bot = ctx.create_bot(base=Bot, adapter=ob12_adapter, **ob12_kwargs())
        message = Message("321")
        message_event = mock_obv12_message_event(message)

        ctx.receive_event(bot, message_event)
        ctx.should_call_api(
            "send_message",
            data={
                "message": Message("123"),
                "detail_type": "private",
                "user_id": message_event.user_id,
            },
            result={"message_id": "12355223"},
        )


async def test_send_active(app: App):
    from nonebot import get_driver

    from nonebot_plugin_saa import (
        TargetQQGroup,
        MessageFactory,
        TargetQQPrivate,
        TargetOB12Unknow,
        SupportedAdapters,
        TargetQQGuildDirect,
        TargetQQGuildChannel,
    )

    async with app.test_api() as ctx:
        adapter_ob12 = get_driver()._adapters[str(SupportedAdapters.onebot_v12)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_ob12, **ob12_kwargs())

        target = TargetQQGroup(group_id=2233)
        ctx.should_call_api(
            "send_message",
            data={
                "message": Message("123"),
                "detail_type": "group",
                "group_id": "2233",
            },
            result={"message_id": "12355223"},
        )
        await MessageFactory("123").send_to(target, bot)

        target = TargetQQPrivate(user_id=1122)
        ctx.should_call_api(
            "send_message",
            data={
                "message": Message("123"),
                "detail_type": "private",
                "user_id": "1122",
            },
            result={"message_id": "12355223"},
        )
        await MessageFactory("123").send_to(target, bot)

        target = TargetOB12Unknow(
            platform="unknow", detail_type="channel", channel_id="3344"
        )
        ctx.should_call_api(
            "send_message",
            data={
                "message": Message("123"),
                "detail_type": "channel",
                "channel_id": "3344",
                "guild_id": None,
                "user_id": None,
                "group_id": None,
            },
            result={"message_id": "12355223"},
        )
        await MessageFactory("123").send_to(target, bot)

        bot.platform = "qqguild"
        target = TargetQQGuildDirect(recipient_id=1111, source_guild_id=2222)
        ctx.should_call_api(
            "create_dms",
            data={
                "user_id": "1111",
                "src_guild_id": "2222",
            },
            result={"guild_id": "3333"},
        )
        ctx.should_call_api(
            "send_message",
            data={
                "message": Message("123"),
                "guild_id": "3333",
                "detail_type": "private",
            },
            result={"message_id": "12355223"},
        )
        await MessageFactory("123").send_to(target, bot)

        target = TargetQQGuildChannel(channel_id=4444)
        ctx.should_call_api(
            "send_message",
            data={
                "message": Message("123"),
                "detail_type": "channel",
                "channel_id": "4444",
            },
            result={"message_id": "12355223"},
        )
        await MessageFactory("123").send_to(target, bot)


async def test_list_targets(app: App, mocker: MockerFixture):
    from nonebot_plugin_saa.auto_select_bot import NoBotFound, get_bot, refresh_bots
    from nonebot_plugin_saa import (
        TargetQQGroup,
        TargetQQPrivate,
        TargetOB12Unknow,
        TargetQQGuildChannel,
    )

    mocker.patch("nonebot_plugin_saa.auto_select_bot.inited", True)

    async with app.test_api() as ctx:
        adapter = get_adapter(Adapter)
        qq_bot = ctx.create_bot(
            base=Bot, adapter=adapter, platform="qq", impl="walle", self_id="1"
        )
        qqguild_bot = ctx.create_bot(
            base=Bot, adapter=adapter, platform="qqguild", impl="all4one", self_id="2"
        )
        unknown_bot = ctx.create_bot(
            base=Bot, adapter=adapter, platform="test", impl="test", self_id="3"
        )

        # QQ
        ctx.should_call_api("get_friend_list", {}, [{"user_id": "1"}])
        ctx.should_call_api("get_group_list", {}, [{"group_id": "2"}])
        ctx.should_call_api("get_guild_list", {}, [])

        # QQGuild
        ctx.should_call_api("get_friend_list", {}, [])
        ctx.should_call_api("get_group_list", {}, [])
        ctx.should_call_api("get_guild_list", {}, [{"guild_id": "1"}])
        ctx.should_call_api(
            "get_channel_list", {"guild_id": "1"}, [{"channel_id": "2"}]
        )

        # Unknown
        ctx.should_call_api("get_friend_list", {}, [{"user_id": "1"}])
        ctx.should_call_api("get_group_list", {}, [{"group_id": "2"}])
        ctx.should_call_api("get_guild_list", {}, [{"guild_id": "3"}])
        ctx.should_call_api(
            "get_channel_list", {"guild_id": "3"}, [{"channel_id": "4"}]
        )
        await refresh_bots()

        send_target_private = TargetQQPrivate(user_id=1)
        assert qq_bot is get_bot(send_target_private)

        send_target_group = TargetQQGroup(group_id=2)
        assert qq_bot is get_bot(send_target_group)

        send_target_qqguild = TargetQQGuildChannel(channel_id=2)
        assert qqguild_bot is get_bot(send_target_qqguild)

        send_private = TargetOB12Unknow(
            platform="test", detail_type="private", user_id="1"
        )
        assert unknown_bot is get_bot(send_private)

        send_group = TargetOB12Unknow(
            platform="test", detail_type="group", group_id="2"
        )
        assert unknown_bot is get_bot(send_group)

        send_channel = TargetOB12Unknow(
            platform="test", detail_type="channel", channel_id="4", guild_id="3"
        )
        assert unknown_bot is get_bot(send_channel)

        send_missing = TargetOB12Unknow(
            platform="missing", detail_type="private", user_id="1"
        )
        with pytest.raises(NoBotFound):
            get_bot(send_missing)


def test_extract_target(app: App):
    from nonebot.adapters.onebot.v12.event import BotSelf
    from nonebot.adapters.onebot.v12 import (
        Message,
        GroupMessageEvent,
        ChannelCreateEvent,
        ChannelDeleteEvent,
        ChannelMessageEvent,
        FriendDecreaseEvent,
        FriendIncreaseEvent,
        PrivateMessageEvent,
        GroupMessageDeleteEvent,
        GroupMemberDecreaseEvent,
        GroupMemberIncreaseEvent,
        ChannelMessageDeleteEvent,
        PrivateMessageDeleteEvent,
        ChannelMemberDecreaseEvent,
        ChannelMemberIncreaseEvent,
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

    group_message_event = GroupMessageEvent(
        id="1122",
        time=datetime.now(),
        type="message",
        detail_type="group",
        sub_type="",
        message_id="2233",
        self=BotSelf(platform="wechat", user_id="3344"),
        message=Message("123"),
        original_message=Message("123"),
        alt_message="123",
        user_id="3344",
        group_id="1122",
    )
    assert extract_target(group_message_event) == TargetOB12Unknow(
        platform="wechat", detail_type="group", group_id="1122"
    )

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

    private_message_event = PrivateMessageEvent(
        id="1122",
        time=datetime.now(),
        type="message",
        detail_type="private",
        sub_type="",
        message_id="2233",
        self=BotSelf(platform="wechat", user_id="3344"),
        message=Message("123"),
        original_message=Message("123"),
        alt_message="123",
        user_id="3344",
    )
    assert extract_target(private_message_event) == TargetOB12Unknow(
        platform="wechat", detail_type="private", user_id="3344"
    )

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
        platform="qq", detail_type="channel", guild_id="5566", channel_id="6677"
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
        qqguild={  # type: ignore
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
        platform="wechat", detail_type="private", user_id="5566"
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
        platform="wechat", detail_type="private", user_id="5566"
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
        platform="wechat", detail_type="private", user_id="5566"
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
        platform="wechat", detail_type="group", group_id="6677"
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
        platform="wechat", detail_type="group", group_id="6677"
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
        platform="wechat", detail_type="group", group_id="6677"
    )

    channel_create_event = ChannelCreateEvent(
        id="1122",
        time=datetime.now(),
        type="notice",
        detail_type="channel_create",
        sub_type="",
        self=BotSelf(platform="qqguild", user_id="3344"),
        guild_id="6677",
        channel_id="7788",
        operator_id="8899",
    )
    assert extract_target(channel_create_event) == TargetQQGuildChannel(channel_id=7788)

    channel_create_event = ChannelCreateEvent(
        id="1122",
        time=datetime.now(),
        type="notice",
        detail_type="channel_create",
        sub_type="",
        self=BotSelf(platform="wechat", user_id="3344"),
        guild_id="6677",
        channel_id="7788",
        operator_id="8899",
    )
    assert extract_target(channel_create_event) == TargetOB12Unknow(
        platform="wechat", detail_type="channel", guild_id="6677", channel_id="7788"
    )

    channel_delete_event = ChannelDeleteEvent(
        id="1122",
        time=datetime.now(),
        type="notice",
        detail_type="channel_delete",
        sub_type="",
        self=BotSelf(platform="qqguild", user_id="3344"),
        guild_id="6677",
        channel_id="7788",
        operator_id="8899",
    )
    assert extract_target(channel_delete_event) == TargetQQGuildChannel(channel_id=7788)

    channel_delete_event = ChannelDeleteEvent(
        id="1122",
        time=datetime.now(),
        type="notice",
        detail_type="channel_delete",
        sub_type="",
        self=BotSelf(platform="wechat", user_id="3344"),
        guild_id="6677",
        channel_id="7788",
        operator_id="8899",
    )
    assert extract_target(channel_delete_event) == TargetOB12Unknow(
        platform="wechat", detail_type="channel", guild_id="6677", channel_id="7788"
    )

    channel_message_delete_event = ChannelMessageDeleteEvent(
        id="1122",
        time=datetime.now(),
        type="notice",
        detail_type="channel_message_delete",
        sub_type="",
        self=BotSelf(platform="qqguild", user_id="3344"),
        message_id="2233",
        user_id="5566",
        guild_id="6677",
        channel_id="7788",
        operator_id="8899",
    )
    assert extract_target(channel_message_delete_event) == TargetQQGuildChannel(
        channel_id=7788
    )

    channel_message_delete_event = ChannelMessageDeleteEvent(
        id="1122",
        time=datetime.now(),
        type="notice",
        detail_type="channel_message_delete",
        sub_type="",
        self=BotSelf(platform="wechat", user_id="3344"),
        message_id="2233",
        user_id="5566",
        guild_id="6677",
        channel_id="7788",
        operator_id="8899",
    )
    assert extract_target(channel_message_delete_event) == TargetOB12Unknow(
        platform="wechat", detail_type="channel", guild_id="6677", channel_id="7788"
    )

    channel_member_decrease_event = ChannelMemberDecreaseEvent(
        id="1122",
        time=datetime.now(),
        type="notice",
        detail_type="channel_member_decrease",
        sub_type="",
        self=BotSelf(platform="qqguild", user_id="3344"),
        user_id="5566",
        guild_id="6677",
        channel_id="7788",
        operator_id="8899",
    )
    assert extract_target(channel_member_decrease_event) == TargetQQGuildChannel(
        channel_id=7788
    )

    channel_member_decrease_event = ChannelMemberDecreaseEvent(
        id="1122",
        time=datetime.now(),
        type="notice",
        detail_type="channel_member_decrease",
        sub_type="",
        self=BotSelf(platform="wechat", user_id="3344"),
        user_id="5566",
        guild_id="6677",
        channel_id="7788",
        operator_id="8899",
    )
    assert extract_target(channel_member_decrease_event) == TargetOB12Unknow(
        platform="wechat", detail_type="channel", guild_id="6677", channel_id="7788"
    )

    channel_member_increase_event = ChannelMemberIncreaseEvent(
        id="1122",
        time=datetime.now(),
        type="notice",
        detail_type="channel_member_increase",
        sub_type="",
        self=BotSelf(platform="qqguild", user_id="3344"),
        user_id="5566",
        guild_id="6677",
        channel_id="7788",
        operator_id="8899",
    )
    assert extract_target(channel_member_increase_event) == TargetQQGuildChannel(
        channel_id=7788
    )

    channel_member_increase_event = ChannelMemberIncreaseEvent(
        id="1122",
        time=datetime.now(),
        type="notice",
        detail_type="channel_member_increase",
        sub_type="",
        self=BotSelf(platform="wechat", user_id="3344"),
        user_id="5566",
        guild_id="6677",
        channel_id="7788",
        operator_id="8899",
    )
    assert extract_target(channel_member_increase_event) == TargetOB12Unknow(
        platform="wechat", detail_type="channel", guild_id="6677", channel_id="7788"
    )
