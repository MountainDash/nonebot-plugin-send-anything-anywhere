# ruff: noqa: E402
import pytest

pytest.importorskip("nonebot.adapters.kaiheila")

from io import BytesIO
from functools import partial

import nonebot
from nonebug import App
from nonebot import get_driver
from pytest_mock import MockerFixture
from nonebot.adapters.kaiheila import Bot, Adapter
from nonebot.adapters.kaiheila.event import Extra, EventMessage
from nonebot.adapters.kaiheila.api import (
    URL,
    Meta,
    User,
    Guild,
    Channel,
    UserChat,
    TargetInfo,
    GuildsReturn,
    ChannelsReturn,
    UserChatsReturn,
    MessageCreateReturn,
)

from nonebot_plugin_saa.utils import SupportedAdapters
from nonebot_plugin_saa import TargetKaiheilaChannel, TargetKaiheilaPrivate

from .utils import assert_ms


@pytest.fixture(scope="session", autouse=True)
def load_adapters(nonebug_init: None):
    driver = nonebot.get_driver()
    driver.register_adapter(Adapter)


def mock_kaiheila_message_event(channel=False):
    from nonebot.adapters.kaiheila.event import (
        ChannelMessageEvent as KaiheilaChannelMessageEvent,
    )
    from nonebot.adapters.kaiheila.event import (
        PrivateMessageEvent as KaiheilaPrivateMessageEvent,
    )

    if not channel:
        return KaiheilaPrivateMessageEvent(
            channel_type="PERSON",
            type=9,
            target_id="2233",
            content="/abc",
            msg_id="abcdef",
            msg_timestamp=1145141919,
            nonce="abcdef",
            extra=Extra(type=9),  # type: ignore
            user_id="3344",
            sub_type="kmarkdown",
            event=EventMessage(
                type=9,
                author=User(id="3344", username="3344", identify_num="3344"),
                content="/abc",
                kmarkdown={
                    "raw_content": "/abc",
                    "mention_part": [],
                    "mention_role_part": [],
                },
            ),  # type: ignore
            message_type="private",
        )
    else:
        return KaiheilaChannelMessageEvent(
            channel_type="GROUP",
            type=9,
            target_id="1111",
            content="/abc",
            msg_id="abcdef",
            msg_timestamp=1145141919,
            nonce="abcdef",
            extra=Extra(type=9),  # type: ignore
            user_id="3344",
            sub_type="kmarkdown",
            event=EventMessage(
                type=9,
                author=User(id="3344", username="3344", identify_num="3344"),
                content="/abc",
                kmarkdown={
                    "raw_content": "/abc",
                    "mention_part": [],
                    "mention_role_part": [],
                },
            ),  # type: ignore
            message_type="group",
            group_id="1111",
        )


def kaiheila_kwargs(name="2233", token="hhhh"):
    return {"name": name, "token": token}


assert_kaiheila = partial(
    assert_ms, Bot, SupportedAdapters.kaiheila, **kaiheila_kwargs()
)


async def test_text(app: App):
    from nonebot.adapters.kaiheila import MessageSegment

    from nonebot_plugin_saa import Text

    await assert_kaiheila(app, Text("123"), MessageSegment.text("123"))


async def test_image(app: App):
    from nonebot.adapters.kaiheila import MessageSegment

    from nonebot_plugin_saa import Image

    adapter = get_driver()._adapters[str(SupportedAdapters.kaiheila)]
    async with app.test_api() as ctx:
        bot = ctx.create_bot(
            base=Bot, adapter=adapter, self_id="2233", **kaiheila_kwargs()
        )

        data = BytesIO(b"\x89PNG\r")

        ctx.should_call_api(
            "asset_create",
            {"file": ("image", b"\x89PNG\r", "application/octet-stream")},
            URL(url="123"),
        )
        generated_ms = await Image(data).build(bot)
        assert generated_ms == MessageSegment.image("123")


async def test_mention(app: App):
    from nonebot.adapters.kaiheila import MessageSegment

    from nonebot_plugin_saa import Mention

    await assert_kaiheila(
        app, Mention("123"), MessageSegment.KMarkdown("(met)123(met)")
    )


async def test_reply(app: App):
    from nonebot.adapters.kaiheila import MessageSegment

    from nonebot_plugin_saa import Reply

    await assert_kaiheila(app, Reply("123"), MessageSegment.quote("123"))


async def test_send(app: App):
    from nonebot.adapters.kaiheila import Bot
    from nonebot import get_driver, on_message

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters

    matcher = on_message()

    @matcher.handle()
    async def process():
        await MessageFactory(Text("123")).send()

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.kaiheila)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **kaiheila_kwargs())
        msg_event = mock_kaiheila_message_event()
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "directMessage_create",
            data={"type": 1, "content": "123", "target_id": "3344"},
            result=MessageCreateReturn(
                msg_id="adfadf", msg_timestamp=98190, nonce="12adjf"
            ),
        )

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.kaiheila)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **kaiheila_kwargs())
        msg_event = mock_kaiheila_message_event(channel=True)
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "message_create",
            data={"type": 1, "content": "123", "target_id": "1111"},
            result=MessageCreateReturn(
                msg_id="adfadf", msg_timestamp=98190, nonce="12adjf"
            ),
        )


async def test_send_revoke(app: App):
    from nonebot.adapters.kaiheila import Bot
    from nonebot import get_driver, on_message

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters

    matcher = on_message()

    @matcher.handle()
    async def process():
        receipt = await MessageFactory(Text("123")).send(reply=True, at_sender=True)
        await receipt.revoke()

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.kaiheila)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **kaiheila_kwargs())
        msg_event = mock_kaiheila_message_event()
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "directMessage_create",
            data={
                "type": 9,
                "content": "(met)3344(met)123",
                "quote": "abcdef",
                "target_id": "3344",
            },
            result=MessageCreateReturn(
                msg_id="adfadf", msg_timestamp=98190, nonce="12adjf"
            ),
        )
        ctx.should_call_api("message_delete", {"msg_id": "adfadf"})


async def test_send_with_reply(app: App):
    from nonebot.adapters.kaiheila import Bot
    from nonebot import get_driver, on_message

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters

    matcher = on_message()

    @matcher.handle()
    async def process():
        await MessageFactory(Text("123")).send(reply=True, at_sender=True)

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.kaiheila)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **kaiheila_kwargs())
        msg_event = mock_kaiheila_message_event()
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "directMessage_create",
            data={
                "type": 9,
                "content": "(met)3344(met)123",
                "quote": "abcdef",
                "target_id": "3344",
            },
            result=MessageCreateReturn(
                msg_id="adfadf", msg_timestamp=98190, nonce="12adjf"
            ),
        )

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.kaiheila)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **kaiheila_kwargs())
        msg_event = mock_kaiheila_message_event(channel=True)
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "message_create",
            data={
                "type": 9,
                "content": "(met)3344(met)123",
                "quote": "abcdef",
                "target_id": "1111",
            },
            result=MessageCreateReturn(
                msg_id="adfadf", msg_timestamp=98190, nonce="12adjf"
            ),
        )


async def test_send_active(app: App):
    from nonebot import get_driver

    from nonebot_plugin_saa import (
        MessageFactory,
        TargetKaiheilaChannel,
        TargetKaiheilaPrivate,
    )

    async with app.test_api() as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.kaiheila)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **kaiheila_kwargs())

        send_target_private = TargetKaiheilaPrivate(user_id="3344")
        ctx.should_call_api(
            "directMessage_create",
            data={"type": 1, "content": "123", "target_id": "3344"},
            result=MessageCreateReturn(
                msg_id="adfadf", msg_timestamp=98190, nonce="12adjf"
            ),
        )
        await MessageFactory("123").send_to(send_target_private, bot)

        send_target_group = TargetKaiheilaChannel(channel_id="1111")
        ctx.should_call_api(
            "message_create",
            data={"type": 1, "content": "123", "target_id": "1111"},
            result=MessageCreateReturn(
                msg_id="adfadf", msg_timestamp=98190, nonce="12adjf"
            ),
        )
        await MessageFactory("123").send_to(send_target_group, bot)


async def test_list_targets(app: App, mocker: MockerFixture):
    from nonebot_plugin_saa.auto_select_bot import get_bot, refresh_bots

    mocker.patch("nonebot_plugin_saa.auto_select_bot.inited", True)

    async with app.test_api() as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.kaiheila)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **kaiheila_kwargs())

        ctx.should_call_api(
            "guild_list",
            {},
            GuildsReturn(
                meta=Meta(page=1, page_total=1, page_size=20, total=1),
                items=[Guild(id="223")],
            ),
        )
        ctx.should_call_api(
            "channel_list",
            {"guild_id": "223"},
            ChannelsReturn(
                meta=Meta(page=1, page_total=1, page_size=20, total=1),
                items=[Channel(id="112")],
            ),
        )
        ctx.should_call_api(
            "userChat_list",
            {},
            UserChatsReturn(
                meta=Meta(page=1, page_total=1, page_size=20, total=1),
                items=[UserChat(target_info=TargetInfo(id="1122"))],
            ),
        )
        await refresh_bots()

        send_target_channel = TargetKaiheilaChannel(channel_id="112")
        assert bot is get_bot(send_target_channel)

        send_target_private = TargetKaiheilaPrivate(user_id="1122")
        assert bot is get_bot(send_target_private)
