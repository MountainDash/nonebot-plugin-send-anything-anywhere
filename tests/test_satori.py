from io import BytesIO
from pathlib import Path
from datetime import datetime
from functools import partial
from typing import Any, Dict, Literal

import pytest
from nonebug import App
from nonebot import get_adapter
from pytest_mock import MockerFixture
from nonebot.compat import type_validate_python
from nonebot.adapters.satori import Bot, Adapter
from nonebot.adapters.satori.config import ClientInfo

from .utils import assert_ms, mock_satori_message_event

satori_kwargs: Dict[Literal["platform", "info"], Any] = {
    "platform": "qq",
    "info": ClientInfo(port=12345),
}


@pytest.fixture
def assert_satori(app: App):
    from nonebot_plugin_saa import SupportedAdapters

    return partial(
        assert_ms,
        Bot,
        SupportedAdapters.satori,
        **satori_kwargs,
    )


async def test_text(app: App, assert_satori):
    from nonebot.adapters.satori import MessageSegment

    from nonebot_plugin_saa import Text

    await assert_satori(app, Text("123"), MessageSegment.text("123"))


async def test_image(app: App, assert_satori):
    from nonebot.adapters.satori import MessageSegment

    from nonebot_plugin_saa import Image

    await assert_satori(app, Image("123"), MessageSegment.image("123"))
    png_bytes = b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x01\xf4"
    jpg_bytes = b"\xff\xd8\xff"
    await assert_satori(
        app,
        Image(png_bytes),
        MessageSegment.image(raw=png_bytes, mime="image/png"),
    )
    await assert_satori(
        app, Image(jpg_bytes), MessageSegment.image(raw=jpg_bytes, mime="image/jpeg")
    )
    await assert_satori(
        app,
        Image(BytesIO(png_bytes)),
        MessageSegment.image(raw=BytesIO(png_bytes), mime="image/png"),
    )
    await assert_satori(
        app, Image(Path("a.png")), MessageSegment.image(path=Path("a.png"))
    )
    with pytest.raises(ValueError, match="Cannot determine image format"):
        await assert_satori(app, Image(b"123"), MessageSegment.image("123"))
    with pytest.raises(ValueError, match="Unsupported image data type"):
        await assert_satori(app, Image(123), MessageSegment.image(123))  # type: ignore


async def test_mention(app: App, assert_satori):
    from nonebot.adapters.satori import MessageSegment

    from nonebot_plugin_saa import Mention

    await assert_satori(app, Mention("123"), MessageSegment.at("123"))


async def test_reply(app: App, assert_satori):
    from nonebot.adapters.satori import MessageSegment

    from nonebot_plugin_saa import Reply
    from nonebot_plugin_saa.adapters.satori import SatoriMessageId

    await assert_satori(
        app, Reply(SatoriMessageId(message_id="123")), MessageSegment.quote("123")
    )


async def test_send(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.satori import Bot, MessageEvent
    from nonebot.adapters.satori.models import InnerMessage

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters

    matcher = on_message()

    @matcher.handle()
    async def process(msg: MessageEvent):
        await MessageFactory(Text("123")).send()

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.satori)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **satori_kwargs)
        msg_event = mock_satori_message_event()
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "message_create",
            {
                "channel_id": "67890",
                "content": "123",
            },
            [InnerMessage(id="321", content="321").model_dump()],
        )


async def test_extract_message_id(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.satori import Bot, MessageEvent
    from nonebot.adapters.satori.models import InnerMessage

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters
    from nonebot_plugin_saa.adapters.satori import SatoriReceipt, SatoriMessageId

    matcher = on_message()

    @matcher.handle()
    async def process(msg: MessageEvent):
        rc = await MessageFactory(Text("123")).send()
        assert isinstance(rc, SatoriReceipt)
        assert rc.extract_message_id() == SatoriMessageId(message_id="321")

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.satori)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **satori_kwargs)
        msg_event = mock_satori_message_event()
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "message_create",
            {
                "channel_id": "67890",
                "content": "123",
            },
            [InnerMessage(id="321", content="321").model_dump()],
        )


async def test_send_with_reply_and_revoke(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.satori import Bot, MessageEvent
    from nonebot.adapters.satori.models import Channel, ChannelType, InnerMessage

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters

    matcher = on_message()

    @matcher.handle()
    async def process(msg: MessageEvent):
        rc = await MessageFactory(Text("123")).send()
        await rc.revoke()

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.satori)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **satori_kwargs)
        msg_event = mock_satori_message_event(public=True)
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "message_create",
            {
                "channel_id": "67890",
                "content": "123",
            },
            [
                InnerMessage(
                    id="321",
                    content="321",
                    channel=Channel(id="67890", type=ChannelType.TEXT),
                ).model_dump()
            ],
        )

        ctx.should_call_api(
            "message_delete", {"channel_id": "67890", "message_id": "321"}
        )


async def test_send_active(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.satori import Bot, MessageEvent
    from nonebot.adapters.satori.models import InnerMessage

    from nonebot_plugin_saa import (
        Text,
        TargetQQGroup,
        MessageFactory,
        TargetQQPrivate,
        SupportedAdapters,
        TargetSatoriUnknown,
    )

    matcher = on_message()

    @matcher.handle()
    async def process(msg: MessageEvent):
        await MessageFactory(Text("123")).send()

    async with app.test_api() as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.satori)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **satori_kwargs)

        send_target_qq_group = TargetQQGroup(group_id=12345)
        send_target_qq_private = TargetQQPrivate(user_id=12345)
        send_target_satori_unknown = TargetSatoriUnknown(
            platform="fake", channel_id="67890", guild_id="12345", user_id="x"
        )
        ctx.should_call_api(
            "message_create",
            {
                "channel_id": "12345",
                "content": "123",
            },
            [InnerMessage(id="321", content="321").model_dump()],
        )
        await MessageFactory(Text("123")).send_to(send_target_qq_group, bot)

        ctx.should_call_api(
            "message_create",
            {
                "channel_id": "private:12345",
                "content": "123",
            },
            [InnerMessage(id="321", content="321").model_dump()],
        )
        await MessageFactory(Text("123")).send_to(send_target_qq_private, bot)

        ctx.should_call_api(
            "message_create",
            {
                "channel_id": "67890",
                "content": "123",
            },
            [InnerMessage(id="321", content="321").model_dump()],
        )
        await MessageFactory(Text("123")).send_to(send_target_satori_unknown, bot)


async def test_send_aggreted_satori(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.satori import Bot, MessageEvent
    from nonebot.adapters.satori.models import InnerMessage

    from nonebot_plugin_saa import Text, SupportedAdapters, AggregatedMessageFactory

    matcher = on_message()

    @matcher.handle()
    async def process(msg: MessageEvent):
        await AggregatedMessageFactory([Text("123"), Text("456")]).send()

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.satori)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **satori_kwargs)
        msg_event = mock_satori_message_event()
        ctx.should_call_api(
            "message_create",
            {
                "channel_id": "67890",
                "content": "<message>123</message><message>456</message>",
            },
            [InnerMessage(id="321", content="321").model_dump()],
        )
        ctx.receive_event(bot, msg_event)


async def test_list_targets(app: App, mocker: MockerFixture):
    from nonebot.exception import ActionFailed
    from nonebot.adapters.satori.models import (
        User,
        Guild,
        Channel,
        PageResult,
        ChannelType,
    )

    from nonebot_plugin_saa.auto_select_bot import BOT_CACHE, get_bot, refresh_bots
    from nonebot_plugin_saa import TargetQQGroup, TargetQQPrivate, SupportedAdapters

    mocker.patch("nonebot_plugin_saa.auto_select_bot.inited", True)

    async with app.test_api() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter, **satori_kwargs)

        ctx.should_call_api(
            "guild_list",
            {"next_token": None},
            exception=ActionFailed(SupportedAdapters.satori),
        )
        ctx.should_call_api(
            "friend_list",
            {"next_token": None},
            exception=ActionFailed(SupportedAdapters.satori),
        )
        await refresh_bots()
        assert not BOT_CACHE.get(bot)

        ctx.should_call_api(
            "guild_list", {"next_token": None}, PageResult(data=[Guild(id="112")])
        )
        ctx.should_call_api(
            "channel_list",
            {"next_token": None, "guild_id": "112"},
            PageResult(data=[Channel(id="112", type=ChannelType.TEXT)]),
        )
        ctx.should_call_api(
            "friend_list",
            {"next_token": None},
            PageResult(data=[User(id="1122")]),
        )
        await refresh_bots()

        send_target_private = TargetQQPrivate(user_id=1122)
        assert bot is get_bot(send_target_private)

        send_target_group = TargetQQGroup(group_id=112)
        assert bot is get_bot(send_target_group)


def test_extract_target(app: App):
    from nonebot.adapters.satori.event import (
        PublicMessageCreatedEvent,
        PrivateMessageCreatedEvent,
    )

    from nonebot_plugin_saa import (
        TargetQQGroup,
        TargetQQPrivate,
        TargetFeishuGroup,
        TargetFeishuPrivate,
        TargetSatoriUnknown,
        TargetTelegramCommon,
        TargetKaiheilaChannel,
        TargetKaiheilaPrivate,
        extract_target,
    )

    def make_pri_event(platform: str = "test"):
        return type_validate_python(
            PrivateMessageCreatedEvent,
            {
                "id": 1,
                "type": "message-created",
                "platform": platform,
                "self_id": "0",
                "timestamp": 1000 * int(datetime.now().timestamp()),
                "channel": {
                    "id": "67890",
                    "type": 0,
                    "name": "test",
                },
                "user": {
                    "id": "12345",
                    "nick": "test",
                },
                "message": {"id": "abcde", "content": "/test"},
            },
        )

    def make_pub_event(platform: str = "test"):
        return type_validate_python(
            PublicMessageCreatedEvent,
            {
                "id": 1,
                "type": "message-created",
                "platform": platform,
                "self_id": "0",
                "timestamp": 1000 * int(datetime.now().timestamp()),
                "channel": {
                    "id": "67890",
                    "type": 0,
                    "name": "test",
                },
                "user": {
                    "id": "12345",
                    "nick": "test",
                },
                "member": {
                    "user": {
                        "id": "12345",
                        "nick": "test",
                    },
                    "nick": "test",
                    "joined_at": 1000 * int(datetime.now().timestamp()),
                },
                "message": {"id": "abcde", "content": "/test"},
            },
        )

    assert extract_target(make_pri_event("qq")) == TargetQQPrivate(user_id=12345)
    assert extract_target(make_pub_event("qq")) == TargetQQGroup(group_id=67890)
    assert extract_target(make_pri_event("feishu")) == TargetFeishuPrivate(
        open_id="12345"
    )
    assert extract_target(make_pub_event("feishu")) == TargetFeishuGroup(
        chat_id="67890"
    )
    assert extract_target(make_pri_event("telegram")) == TargetTelegramCommon(
        chat_id="12345"
    )
    # TODO: support telegram group
    assert extract_target(make_pub_event("telegram")) == TargetSatoriUnknown(
        platform="telegram", channel_id="67890"
    )
    # assert extract_target(make_pub_event("telegram")) == TargetTelegramCommon(
    #     chat_id="12345"
    # )
    assert extract_target(make_pri_event("kook")) == TargetKaiheilaPrivate(
        user_id="12345"
    )
    assert extract_target(make_pub_event("kook")) == TargetKaiheilaChannel(
        channel_id="67890"
    )
    assert extract_target(make_pri_event("unknown")) == TargetSatoriUnknown(
        platform="unknown", channel_id="67890"
    )
    assert extract_target(make_pub_event("unknown")) == TargetSatoriUnknown(
        platform="unknown", channel_id="67890"
    )
