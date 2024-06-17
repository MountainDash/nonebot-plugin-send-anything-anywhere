from io import BytesIO
from pathlib import Path
from datetime import datetime
from functools import partial
from dataclasses import dataclass

import pytest
from nonebug import App
from grpclib.client import Channel
from pytest_mock import MockerFixture
from nonebot.adapters.kritor import Bot
from nonebot.compat import type_validate_python
from nonebot.adapters.kritor.config import ClientInfo

from .utils import assert_ms, mock_kritor_message_event

kritor_bot_config = ClientInfo(
    host="localhost",
    port=8080,
    account="1919810",
    ticket="233333",
)
kritor_kwargs = {
    "self_id": "1919810",
    "info": kritor_bot_config,
    "client": Channel("localhost", 8080),
}


@pytest.fixture
def assert_kritor(app: App):
    from nonebot_plugin_saa import SupportedAdapters

    return partial(
        assert_ms,
        Bot,
        SupportedAdapters.kritor,
        **kritor_kwargs,
    )


async def test_text(app: App, assert_kritor):
    from nonebot.adapters.kritor import MessageSegment

    from nonebot_plugin_saa import Text

    await assert_kritor(
        app, Text("Hello, World!"), MessageSegment.text("Hello, World!")
    )


async def test_image(app: App, assert_kritor, tmp_path: Path):
    from nonebot.adapters.kritor import MessageSegment

    from nonebot_plugin_saa import Image

    tmp_image = tmp_path / "image.jpg"
    tmp_image.write_bytes(b"Hello, World!")

    await assert_kritor(
        app,
        Image("https://example.com/image.jpg"),
        MessageSegment.image(url="https://example.com/image.jpg"),
    )
    await assert_kritor(
        app,
        Image("http://example.com/image.jpg"),
        MessageSegment.image(url="http://example.com/image.jpg"),
    )
    await assert_kritor(
        app,
        Image(tmp_image.as_posix()),
        MessageSegment.image(path=tmp_image.as_posix()),
    )
    await assert_kritor(app, Image(tmp_image), MessageSegment.image(path=tmp_image))
    await assert_kritor(
        app, Image(b"Hello, World!"), MessageSegment.image(raw=b"Hello, World!")
    )
    await assert_kritor(
        app,
        Image(BytesIO(b"Hello, World!")),
        MessageSegment.image(raw=BytesIO(b"Hello, World!")),
    )
    with pytest.raises(TypeError, match="Invalid image str"):
        await assert_kritor(app, Image("Hello, World!"), None)

    with pytest.raises(TypeError, match="Unsupported type of"):
        await assert_kritor(app, Image(123), None)  # type: ignore


async def test_mention(app: App, assert_kritor):
    from nonebot.adapters.kritor import MessageSegment

    from nonebot_plugin_saa import Mention

    await assert_kritor(
        app,
        Mention("123"),
        MessageSegment.at(uid="123"),
    )


async def test_mention_all(app: App, assert_kritor):
    from nonebot.adapters.kritor import MessageSegment

    from nonebot_plugin_saa import MentionAll

    await assert_kritor(
        app,
        MentionAll(),
        MessageSegment.atall(),
    )


async def test_reply(app: App, assert_kritor):
    from nonebot.adapters.kritor import MessageSegment

    from nonebot_plugin_saa import Reply
    from nonebot_plugin_saa.adapters.kritor import KritorMessageId

    await assert_kritor(
        app,
        Reply(KritorMessageId(message_id="123")),
        MessageSegment.reply(message_id="123"),
    )


async def test_send(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.kritor import Bot, Message
    from nonebot.adapters.kritor.model import Group, Guild, Friend
    from nonebot.adapters.kritor.protos.kritor.message import SendMessageResponse
    from nonebot.adapters.kritor.protos.kritor.guild import SendChannelMessageResponse
    from nonebot.adapters.kritor.event import GroupMessage, GuildMessage, FriendMessage

    from nonebot_plugin_saa.registries import SaaMessageId
    from nonebot_plugin_saa.adapters.kritor import KritorMessageId
    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters

    adapter_obj = get_driver()._adapters[str(SupportedAdapters.kritor)]

    # FIXME: 当前Kritor适配器在nonebug中在一个matcher里
    # 定义两个处理不同消息事件的业务函数会出现问题，暂时分开测试

    matcher1 = on_message()

    @matcher1.handle()
    async def fprocess(msg: FriendMessage, mid: SaaMessageId):
        assert mid == KritorMessageId(message_id=msg.message_id)
        await MessageFactory(Text("Hello, Friend!")).send()

    async with app.test_matcher(matcher1) as ctx:
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **kritor_kwargs)
        msg_event = mock_kritor_message_event(
            Friend(peer="111", sub_peer=None), Message("Hello, Friend!")
        )
        assert msg_event
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "send_message",
            data={
                "contact": Friend(peer="111", sub_peer=None),
                "elements": Message("Hello, Friend!").to_elements(),
                "message_id": "1234",
            },
            result=SendMessageResponse(message_id="1234", message_time=1234567890),
        )

    matcher2 = on_message()

    @matcher2.handle()
    async def gprocess(msg: GroupMessage):
        await MessageFactory(Text("Hello, Group!")).send()

    async with app.test_matcher(matcher2) as ctx:
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **kritor_kwargs)

        msg_event2 = mock_kritor_message_event(
            Group(peer="222", sub_peer=None), Message("Hello, World!")
        )
        ctx.receive_event(bot, msg_event2)
        ctx.should_call_api(
            "send_message",
            data={
                "contact": Group(peer="222", sub_peer=None),
                "elements": Message("Hello, Group!").to_elements(),
                "message_id": "1234",
            },
            result=SendMessageResponse(message_id="1234", message_time=1234567890),
        )

    matcher3 = on_message()

    @matcher3.handle()
    async def cprocess(msg: GuildMessage):
        await MessageFactory(Text("Hello, Guild!")).send()

    async with app.test_matcher(matcher3) as ctx:
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **kritor_kwargs)

        msg_event3 = mock_kritor_message_event(
            Guild(peer="333", sub_peer="444"), Message("Hello, World!")
        )
        ctx.receive_event(bot, msg_event3)
        ctx.should_call_api(
            "send_channel_message",
            data={
                "guild_id": 333,
                "channel_id": 444,
                "message": str(Message("Hello, Guild!")),
            },
            result=SendChannelMessageResponse(
                message_id="1234", message_time=1234567890
            ),
        )


async def test_receipt_operation(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.kritor.model import Group
    from nonebot.adapters.kritor import Bot, Message
    from nonebot.adapters.kritor.event import GroupMessage
    from nonebot.adapters.kritor.protos.kritor.message import SendMessageResponse

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters
    from nonebot_plugin_saa.adapters.kritor import KritorReceipt, KritorMessageId

    matcher = on_message()

    @matcher.handle()
    async def fprocess(msg: GroupMessage):
        receipt = await MessageFactory(Text("Hello, Friend!")).send()
        assert isinstance(receipt, KritorReceipt)
        assert receipt.extract_message_id() == KritorMessageId(message_id="1234")
        await receipt.essence()
        await receipt.unessence()
        assert await receipt.get_message()
        await receipt.react(1)
        await receipt.react(1, is_set=False)
        assert receipt.raw["message_id"] == "1234"

        await receipt.revoke()

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.kritor)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **kritor_kwargs)
        msg_event = mock_kritor_message_event(
            Group(peer="111", sub_peer=None), Message("Hello, World!")
        )
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "send_message",
            data={
                "contact": Group(peer="111", sub_peer=None),
                "elements": Message("Hello, Friend!").to_elements(),
                "message_id": "1234",
            },
            result=SendMessageResponse(message_id="1234", message_time=1234567890),
        )

        ctx.should_call_api(
            "set_essence_message",
            data={"message_id": "1234", "group_id": Group(peer="111", sub_peer=None)},
        )
        ctx.should_call_api(
            "delete_essence_message",
            data={"message_id": "1234", "group_id": Group(peer="111", sub_peer=None)},
        )
        ctx.should_call_api("get_message", data={"message_id": "1234"}, result=True)
        ctx.should_call_api(
            "set_message_comment_emoji",
            data={
                "contact": Group(peer="111", sub_peer=None),
                "message_id": "1234",
                "emoji": 1,
                "is_set": True,
            },
        )
        ctx.should_call_api(
            "set_message_comment_emoji",
            data={
                "contact": Group(peer="111", sub_peer=None),
                "message_id": "1234",
                "emoji": 1,
                "is_set": False,
            },
        )
        ctx.should_call_api(
            "recall_message",
            data={"message_id": "1234"},
        )


async def test_send_active(app: App):
    from nonebot import get_driver
    from nonebot.adapters.kritor import Bot, Message
    from nonebot.adapters.kritor.model import Contact
    from nonebot.adapters.kritor.protos.kritor.message import SendMessageResponse

    from nonebot_plugin_saa import (
        TargetQQGroup,
        MessageFactory,
        TargetQQPrivate,
        SupportedAdapters,
        TargetKritorUnknown,
        TargetQQGuildChannel,
    )

    async with app.test_api() as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.kritor)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **kritor_kwargs)

        send_target_private = TargetQQPrivate(user_id=1122)
        ctx.should_call_api(
            "send_message",
            data={
                "contact": type_validate_python(
                    Contact, send_target_private.arg_dict(bot)
                ),
                "elements": Message("123").to_elements(),
                "message_id": None,
            },
            result=SendMessageResponse(message_id="1234", message_time=1234567890),
        )
        await MessageFactory("123").send_to(send_target_private, bot)

        send_target_group = TargetQQGroup(group_id=3344)
        ctx.should_call_api(
            "send_message",
            data={
                "contact": type_validate_python(
                    Contact, send_target_group.arg_dict(bot)
                ),
                "elements": Message("123").to_elements(),
                "message_id": None,
            },
            result=SendMessageResponse(message_id="1234", message_time=1234567890),
        )
        await MessageFactory("123").send_to(send_target_group, bot)

        send_target_guild_channel = TargetQQGuildChannel(
            guild_id="5566", channel_id=7788
        )
        ctx.should_call_api(
            "send_channel_message",
            data={
                "guild_id": 5566,
                "channel_id": 7788,
                "message": "123",
            },
            result=SendMessageResponse(message_id="1234", message_time=1234567890),
        )
        await MessageFactory("123").send_to(send_target_guild_channel, bot)

        send_target_unknown = TargetKritorUnknown(
            type="0", primary_id="9900", secondary_id="1011"
        )
        ctx.should_call_api(
            "send_message",
            data={
                "contact": type_validate_python(
                    Contact, send_target_unknown.arg_dict(bot)
                ),
                "elements": Message("123").to_elements(),
                "message_id": None,
            },
            result=SendMessageResponse(message_id="1234", message_time=1234567890),
        )
        await MessageFactory("123").send_to(send_target_unknown, bot)


async def test_send_aggreted(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.kritor.model import Friend
    from nonebot.adapters.kritor import Bot, Message, MessageEvent
    from nonebot.adapters.kritor.protos.kritor.common import (
        Sender,
        PushMessageBody,
        ForwardMessageBody,
    )

    from nonebot_plugin_saa import Text, SupportedAdapters, AggregatedMessageFactory

    matcher = on_message()

    @matcher.handle()
    async def process(msg: MessageEvent):
        await AggregatedMessageFactory(
            [
                Text("111"),
                Text("222"),
                Text("333"),
            ]
        ).send()

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.kritor)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **kritor_kwargs)
        msg_event = mock_kritor_message_event(
            Friend(peer="111", sub_peer=None),
            Message("Hello, World!"),
        )

        forward_msg_list = []
        ms = [
            Message("111"),
            Message("222"),
            Message("333"),
        ]
        for m in ms:
            forward_msg_list.append(
                ForwardMessageBody(
                    message=PushMessageBody(
                        time=int(datetime.now().timestamp()),
                        sender=Sender(
                            uid="1919810",
                            uin=1919810,
                            nick="NoneBot",
                        ),
                        elements=m.to_elements(),
                    )
                )
            )

        @dataclass
        class FakeInfo:
            nickname: str = "NoneBot"

        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "get_bot_info",
            data={},
            result=FakeInfo(),
        )
        ctx.should_call_api(
            "upload_forward_message",
            data={
                "contact": Friend(peer="111", sub_peer=None),
                "messages": forward_msg_list,
            },
        )


async def test_send_aggreted_active(app: App):
    from nonebot import get_driver
    from nonebot.adapters.kritor import Bot, Message
    from nonebot.adapters.kritor.model import Contact
    from nonebot.adapters.kritor.protos.kritor.common import (
        Sender,
        PushMessageBody,
        ForwardMessageBody,
    )

    from nonebot_plugin_saa import (
        Text,
        TargetQQPrivate,
        SupportedAdapters,
        AggregatedMessageFactory,
    )

    forward_msg_list = []
    ms = [
        Message("111"),
        Message("222"),
        Message("333"),
    ]
    for m in ms:
        forward_msg_list.append(
            ForwardMessageBody(
                message=PushMessageBody(
                    time=int(datetime.now().timestamp()),
                    sender=Sender(
                        uid="1919810",
                        uin=1919810,
                        nick="NoneBot",
                    ),
                    elements=m.to_elements(),
                )
            )
        )

    async with app.test_api() as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.kritor)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **kritor_kwargs)
        send_target = TargetQQPrivate(user_id=111)

        @dataclass
        class FakeInfo:
            nickname: str = "NoneBot"

        ctx.should_call_api(
            "get_bot_info",
            data={},
            result=FakeInfo(),
        )

        ctx.should_call_api(
            "upload_forward_message",
            data={
                "contact": type_validate_python(Contact, send_target.arg_dict(bot)),
                "messages": forward_msg_list,
            },
        )
        await AggregatedMessageFactory(
            [
                Text("111"),
                Text("222"),
                Text("333"),
            ]
        ).send_to(send_target, bot)


async def test_list_targets(app: App, mocker: MockerFixture):
    from nonebot import get_driver
    from nonebot.adapters.kritor.protos.kritor.group import GroupInfo
    from nonebot.adapters.kritor.protos.kritor.friend import FriendInfo
    from nonebot.adapters.kritor.protos.kritor.guild import GuildInfo, ChannelInfo

    from nonebot_plugin_saa.auto_select_bot import (
        BOT_CACHE,
        NoBotFound,
        get_bot,
        refresh_bots,
    )
    from nonebot_plugin_saa import (
        TargetQQGroup,
        TargetQQPrivate,
        SupportedAdapters,
        TargetQQGuildChannel,
    )

    mocker.patch("nonebot_plugin_saa.auto_select_bot.inited", True)

    async with app.test_api() as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.kritor)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **kritor_kwargs)

        ctx.should_call_api(
            "get_friend_list",
            data={},
            result=[
                FriendInfo(
                    uid="1122",
                    uin=1122,
                    nick="Alice",
                ),
                FriendInfo(
                    uid="3344",
                    uin=3344,
                    nick="Bob",
                ),
            ],
        )
        ctx.should_call_api(
            "get_group_list",
            data={},
            result=[
                GroupInfo(
                    group_id=5566,
                    group_name="Group1",
                ),
                GroupInfo(
                    group_id=7788,
                    group_name="Group2",
                ),
            ],
        )
        ctx.should_call_api(
            "get_guild_list",
            data={},
            result=[
                GuildInfo(
                    guild_id=9900,
                    guild_name="Guild1",
                ),
                GuildInfo(
                    guild_id=1415,
                    guild_name="Guild2",
                ),
            ],
        )
        ctx.should_call_api(
            "get_guild_channel_list",
            data={"guild_id": 9900},
            result=[
                ChannelInfo(
                    channel_id=1011,
                    channel_name="Channel1",
                ),
                ChannelInfo(
                    channel_id=1213,
                    channel_name="Channel2",
                ),
            ],
        )
        ctx.should_call_api(
            "get_guild_channel_list",
            data={"guild_id": 1415},
            exception=RuntimeError(),
        )

        await refresh_bots()
        assert BOT_CACHE.get(bot)

        send_target_private = TargetQQPrivate(user_id=1122)
        assert bot is get_bot(send_target_private)
        send_target_group = TargetQQGroup(group_id=5566)
        assert bot is get_bot(send_target_group)
        send_target_guild_channel = TargetQQGuildChannel(
            guild_id="9900", channel_id=1011
        )
        assert bot is get_bot(send_target_guild_channel)
        send_target_guild_channel2 = TargetQQGuildChannel(
            guild_id="1415", channel_id=1213
        )
        with pytest.raises(NoBotFound):
            get_bot(send_target_guild_channel2)

        send_target_only_channel = TargetQQGuildChannel(channel_id=1011)
        assert bot is get_bot(send_target_only_channel)

        target_missing = TargetQQGuildChannel(guild_id="1415", channel_id=1415)
        with pytest.raises(NoBotFound):
            get_bot(target_missing)


def test_extract_target(app: App):
    from nonebot.adapters.kritor.message import Message
    from nonebot.adapters.kritor.model import Group, Guild, Friend, Stranger
    from nonebot.adapters.kritor.event import (
        GroupPokeNotice,
        PrivatePokeNotice,
        FriendApplyRequest,
    )

    from nonebot_plugin_saa import (
        TargetQQGroup,
        TargetQQPrivate,
        TargetKritorUnknown,
        TargetQQGuildChannel,
        extract_target,
    )

    assert extract_target(
        mock_kritor_message_event(
            Friend(peer="1122", sub_peer=None),
            Message("Hello, World!"),
        )
    ) == TargetQQPrivate(user_id=1122)

    assert extract_target(
        mock_kritor_message_event(
            Group(peer="3344", sub_peer=None),
            Message("Hello, World!"),
        )
    ) == TargetQQGroup(group_id=3344)

    assert extract_target(
        mock_kritor_message_event(
            Guild(peer="5566", sub_peer="7788"),
            Message("Hello, World!"),
        )
    ) == TargetQQGuildChannel(guild_id="5566", channel_id=7788)

    assert extract_target(
        mock_kritor_message_event(
            Stranger(peer="1122", sub_peer=None),
            Message("Hello, World!"),
        )
    ) == TargetKritorUnknown(type="9", primary_id="1122", secondary_id=None)

    assert extract_target(
        PrivatePokeNotice(
            time=datetime.now(),
            operator_uid="1122",
            operator_uin=1122,
            action="poke",
            to_me=False,
            suffix="",
            action_image="",
        )
    ) == TargetQQPrivate(user_id=1122)

    assert extract_target(
        GroupPokeNotice(
            time=datetime.now(),
            operator_uid="3344",
            operator_uin=3344,
            target_uid="1122",
            target_uin=1122,
            group_id=7788,
            action="poke",
            to_me=False,
            suffix="",
            action_image="",
        )
    ) == TargetQQGroup(group_id=7788)

    assert extract_target(
        FriendApplyRequest(
            time=datetime.now(),
            applier_uid="1122",
            applier_uin=1122,
            message="apply",
            flag="",
        )
    ) == TargetQQPrivate(user_id=1122)
