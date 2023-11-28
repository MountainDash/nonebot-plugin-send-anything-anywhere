from pathlib import Path
from datetime import datetime
from functools import partial

from nonebug import App
from nonebot import get_adapter
from pytest_mock import MockerFixture
from nonebot.adapters.qq import Bot, Adapter
from nonebot.adapters.qq.config import BotInfo
from nonebot.adapters.qq.models import DMS, User, Guild, Channel, Message, QQMessage

from nonebot_plugin_saa.utils import SupportedAdapters

from .utils import assert_ms, mock_qq_message_event, mock_qq_guild_message_event

MockGuild = partial(
    Guild,
    id="1",
    name="test1",
    icon="",
    owner_id="1",
    owner=True,
    member_count=1,
    max_members=1,
    description="",
    joined_at=datetime(2023, 10, 20),
)
MockChannel = partial(
    Channel,
    id="2233",
    guild_id="0",
    name="test1",
    type=0,
    sub_type=0,
    position=0,
    private_type=0,
    speak_permission=0,
)
MockGroup = partial(
    Channel,
    id="2233",
    guild_id="0",
    name="test1",
    type=0,
    sub_type=0,
    position=0,
    private_type=0,
    speak_permission=0,
)
MockQQGuildMessage = partial(
    Message, id="1", channel_id="2233", guild_id="1", author=User(id="1")
)
MockQQMessage = partial(QQMessage, id="1", timestamp="2023-10-20T00:00:00+08:00")

assert_qq = partial(
    assert_ms,
    Bot,
    SupportedAdapters.qq,
    self_id="314159",
    bot_info=BotInfo(id="314159", token="token", secret="secret"),
)


async def test_text(app: App):
    from nonebot.adapters.qq import MessageSegment

    from nonebot_plugin_saa import Text

    await assert_qq(app, Text("text"), MessageSegment.text("text"))


async def test_image(app: App, tmp_path: Path):
    from nonebot.adapters.qq import MessageSegment

    from nonebot_plugin_saa import Image

    await assert_qq(
        app,
        Image("https://picsum.photos/200"),
        MessageSegment.image("https://picsum.photos/200"),
    )

    data = b"\x89PNG\r"
    await assert_qq(app, Image(data), MessageSegment.file_image(data))

    image_path = tmp_path / "image.png"
    with open(image_path, "wb") as f:
        f.write(data)
    await assert_qq(app, Image(image_path), MessageSegment.file_image(image_path))


async def test_mention_user(app: App):
    from nonebot.adapters.qq import MessageSegment

    from nonebot_plugin_saa import Mention

    await assert_qq(app, Mention("314159"), MessageSegment.mention_user("314159"))


async def test_send(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.qq import Bot, Message

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters

    matcher = on_message()

    @matcher.handle()
    async def _():
        await MessageFactory(Text("123")).send()

    async with app.test_matcher(matcher) as ctx:
        qq_adapter = get_driver()._adapters[SupportedAdapters.qq]
        bot = ctx.create_bot(
            base=Bot,
            adapter=qq_adapter,
            self_id="3344",
            bot_info=BotInfo(id="3344", token="", secret=""),
        )

        event = mock_qq_guild_message_event(Message("321"))
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            Message("123"),
            result=MockQQGuildMessage(id="1234871", channel_id=event.channel_id),
        )

        event = mock_qq_guild_message_event(Message("322"), direct=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            Message("123"),
            result=MockQQGuildMessage(id="1234871", channel_id=event.channel_id),
        )

        event = mock_qq_message_event(Message("323"))
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            Message("123"),
            result=MockQQMessage(id="1234871", content="123"),
        )

        event = mock_qq_message_event(Message("323"), direct=True)
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            Message("123"),
            result=MockQQMessage(id="1234871", content="123"),
        )


async def test_send_revoke(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.qq import Bot, Message

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters

    matcher = on_message()

    @matcher.handle()
    async def _():
        receipt = await MessageFactory(Text("123")).send()
        await receipt.revoke()

    async with app.test_matcher(matcher) as ctx:
        qq_adapter = get_driver()._adapters[SupportedAdapters.qq]
        bot = ctx.create_bot(
            base=Bot,
            adapter=qq_adapter,
            self_id="3344",
            bot_info=BotInfo(id="3344", token="", secret=""),
        )

        # only guild message can be revoked
        event = mock_qq_guild_message_event(Message("321"))
        ctx.receive_event(bot, event)
        ctx.should_call_send(
            event,
            Message("123"),
            result=MockQQGuildMessage(id="1234871", channel_id=event.channel_id),
        )
        ctx.should_call_api(
            "delete_message",
            data={
                "channel_id": event.channel_id,
                "message_id": "1234871",
                "hidetip": False,
            },
        )


async def test_send_active(app: App):
    from nonebot import get_driver

    from nonebot_plugin_saa import (
        MessageFactory,
        TargetQQGroupOpenId,
        TargetQQGuildDirect,
        TargetQQGuildChannel,
        TargetQQPrivateOpenId,
    )

    async with app.test_api() as ctx:
        adapter_qq = get_driver()._adapters[str(SupportedAdapters.qq)]
        bot = ctx.create_bot(
            base=Bot,
            adapter=adapter_qq,
            self_id="3344",
            bot_info=BotInfo(id="3344", token="", secret=""),
        )

        ctx.should_call_api(
            "post_messages",
            data={
                "channel_id": "2233",
                "msg_id": None,
                "event_id": None,
                "content": "123",
            },
            result=MockQQGuildMessage(id="1234871", channel_id="2233"),
        )
        target = TargetQQGuildChannel(channel_id=2233)
        await MessageFactory("123").send_to(target, bot)

        target = TargetQQGuildDirect(recipient_id=1111, source_guild_id=2222)
        ctx.should_call_api(
            "post_dms",
            data={
                "recipient_id": "1111",
                "source_guild_id": "2222",
            },
            result=DMS(guild_id="3333"),
        )
        ctx.should_call_api(
            "post_dms_messages",
            data={
                "guild_id": "3333",
                "msg_id": None,
                "event_id": None,
                "content": "123",
            },
            result=MockQQGuildMessage(id="1234871", channel_id="12479234"),
        )
        await MessageFactory("123").send_to(target, bot)
        # 再次发送，这次直接从缓存中获取 guild_id
        ctx.should_call_api(
            "post_dms_messages",
            data={
                "guild_id": "3333",
                "msg_id": None,
                "event_id": None,
                "content": "1234",
            },
            result=MockQQGuildMessage(id="1234871", channel_id="12355131"),
        )
        await MessageFactory("1234").send_to(target, bot)

        ctx.should_call_api(
            "post_group_messages",
            data={
                "group_openid": "2233",
                "msg_type": 0,
                "content": "123",
                "media": None,
                "msg_id": None,
                "msg_seq": None,
                "event_id": None,
            },
            result=MockQQMessage(id="1234871", content="123"),
        )
        target = TargetQQGroupOpenId(bot_id="3344", group_openid="2233")
        await MessageFactory("123").send_to(target, bot)

        ctx.should_call_api(
            "post_c2c_messages",
            data={
                "openid": "2233",
                "msg_type": 0,
                "content": "123",
                "media": None,
                "msg_id": None,
                "msg_seq": None,
                "event_id": None,
            },
            result=MockQQMessage(id="1234871", content="123"),
        )
        target = TargetQQPrivateOpenId(bot_id="3344", user_openid="2233")
        await MessageFactory("123").send_to(target, bot)


async def test_list_targets(app: App, mocker: MockerFixture):
    from nonebot_plugin_saa import TargetQQGuildChannel
    from nonebot_plugin_saa.auto_select_bot import get_bot, refresh_bots

    mocker.patch("nonebot_plugin_saa.auto_select_bot.inited", True)

    async with app.test_api() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=Bot,
            adapter=adapter,
            self_id="3344",
            bot_info=BotInfo(id="3344", token="", secret=""),
        )

        # only private-domain guild bot can get target list
        ctx.should_call_api("guilds", {}, [MockGuild(id="1", name="test1")])
        ctx.should_call_api(
            "get_channels", {"guild_id": "1"}, [MockChannel(id="2233", name="test1")]
        )
        await refresh_bots()

        target = TargetQQGuildChannel(channel_id=2233)
        assert bot is get_bot(target)


async def test_extract_target(app: App):
    from nonebot import get_driver
    from nonebot.adapters.qq.models import FriendAuthor, GroupMemberAuthor
    from nonebot.adapters.qq import (
        EventType,
        MessageCreateEvent,
        C2CMessageCreateEvent,
        DirectMessageCreateEvent,
        GroupAtMessageCreateEvent,
    )

    from nonebot_plugin_saa import (
        SupportedAdapters,
        TargetQQGroupOpenId,
        TargetQQGuildDirect,
        TargetQQGuildChannel,
        TargetQQPrivateOpenId,
        extract_target,
    )

    async with app.test_api() as ctx:
        qq_adapter = get_driver()._adapters[SupportedAdapters.qq]
        bot = ctx.create_bot(
            base=Bot,
            adapter=qq_adapter,
            self_id="3344",
            bot_info=BotInfo(id="3344", token="", secret=""),
        )

        guild_message_event = MessageCreateEvent(
            __type__=EventType.CHANNEL_CREATE,
            id="1",
            channel_id="6677",
            guild_id="5566",
            author=User(id="1"),
        )

        assert extract_target(guild_message_event) == TargetQQGuildChannel(
            channel_id=6677
        )
        assert extract_target(guild_message_event, bot) == TargetQQGuildChannel(
            channel_id=6677
        )

        direct_message_event = DirectMessageCreateEvent(
            __type__=EventType.DIRECT_MESSAGE_CREATE,
            id="1",
            channel_id="6677",
            guild_id="5566",
            author=User(id="1"),
        )

        assert extract_target(direct_message_event, bot) == TargetQQGuildDirect(
            recipient_id=1, source_guild_id=5566
        )

        c2c_message_event = C2CMessageCreateEvent(
            __type__=EventType.C2C_MESSAGE_CREATE,
            id="1",
            author=FriendAuthor(id="CCDD", user_openid="CCDD"),
            content="test",
            timestamp="12345678",
        )

        assert extract_target(c2c_message_event, bot) == TargetQQPrivateOpenId(
            bot_id="3344", user_openid="CCDD"
        )

        group_at_message_event = GroupAtMessageCreateEvent(
            __type__=EventType.GROUP_AT_MESSAGE_CREATE,
            id="1",
            author=GroupMemberAuthor(id="3344", member_openid="3344"),
            group_openid="AABB",
            content="test",
            timestamp="12345678",
        )

        assert extract_target(group_at_message_event, bot) == TargetQQGroupOpenId(
            bot_id="3344", group_openid="AABB"
        )


async def test_target_dependency_injection(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.qq import (
        Message,
        MessageCreateEvent,
        C2CMessageCreateEvent,
        DirectMessageCreateEvent,
        GroupAtMessageCreateEvent,
    )

    from nonebot_plugin_saa import (
        SaaTarget,
        SupportedAdapters,
        TargetQQGroupOpenId,
        TargetQQGuildDirect,
        TargetQQGuildChannel,
        TargetQQPrivateOpenId,
    )

    matcher = on_message()

    @matcher.handle()
    async def _(event: MessageCreateEvent, target: SaaTarget):
        assert event
        assert isinstance(target, TargetQQGuildChannel)

    @matcher.handle()
    async def _(event: DirectMessageCreateEvent, target: SaaTarget):
        assert event
        assert isinstance(target, TargetQQGuildDirect)

    @matcher.handle()
    async def _(event: GroupAtMessageCreateEvent, target: SaaTarget):
        assert event
        assert isinstance(target, TargetQQGroupOpenId)

    @matcher.handle()
    async def _(event: C2CMessageCreateEvent, target: SaaTarget):
        assert event
        assert isinstance(target, TargetQQPrivateOpenId)

    async with app.test_matcher(matcher) as ctx:
        qq_adapter = get_driver()._adapters[SupportedAdapters.qq]
        bot = ctx.create_bot(
            base=Bot,
            adapter=qq_adapter,
            self_id="3344",
            bot_info=BotInfo(id="3344", token="", secret=""),
        )

        event = mock_qq_guild_message_event(Message("321"))
        ctx.receive_event(bot, event)
        event = mock_qq_guild_message_event(Message("321"), direct=True)
        ctx.receive_event(bot, event)
        event = mock_qq_message_event(Message("321"))
        ctx.receive_event(bot, event)
        event = mock_qq_message_event(Message("321"), direct=True)
        ctx.receive_event(bot, event)
