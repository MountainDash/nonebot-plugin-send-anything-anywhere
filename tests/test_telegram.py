from functools import partial
from typing import Any, cast

from nonebot.adapters.telegram import Bot
from nonebot.adapters.telegram.config import BotConfig
from nonebot_plugin_saa.utils import SupportedAdapters
from nonebug import App

from .utils import assert_ms, mock_telegram_message_event

BOT_CONFIG = BotConfig(token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")
assert_telegram = partial(
    assert_ms,
    Bot,
    SupportedAdapters.telegram,
    config=BOT_CONFIG,
)


async def test_text(app: App):
    from nonebot.adapters.telegram.message import Entity
    from nonebot_plugin_saa import Text

    await assert_telegram(app, Text("114514"), Entity.text("114514"))


async def test_image(app: App):
    from nonebot.adapters.telegram.message import File
    from nonebot_plugin_saa import Image

    await assert_telegram(app, Image("114514"), File.photo("114514"))


async def test_mention(app: App):
    from nonebot.adapters.telegram.message import Entity
    from nonebot_plugin_saa import Mention

    await assert_telegram(app, Mention("@senpai"), Entity.mention("@senpai "))

    await assert_telegram(
        app,
        Mention("114514"),
        Entity.text_link("用户 ", "tg://user?id=114514"),
    )


async def test_reply(app: App):
    from nonebot.adapters.telegram.message import MessageSegment
    from nonebot_plugin_saa import Reply

    await assert_telegram(
        app,
        Reply(114514),
        MessageSegment("reply", {"message_id": "114514"}),
    )


async def test_send(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.telegram import Bot, Message
    from nonebot.adapters.telegram.event import MessageEvent
    from nonebot_plugin_saa import MessageFactory, SupportedAdapters, Text

    matcher = on_message()

    @matcher.handle()
    async def _(ev: MessageEvent):
        await MessageFactory(
            [Text(f"homo senpai {ev.message.extract_plain_text()}")]
        ).send()

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.telegram)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, config=BOT_CONFIG)

        msg_event = mock_telegram_message_event(Message("114514"))
        ctx.receive_event(bot, msg_event)
        ctx.should_call_send(
            msg_event,
            Message("homo senpai 114514"),
            None,
            reply_to_message_id=None,
        )


async def test_send_with_reply(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.telegram import Bot, Message
    from nonebot.adapters.telegram.event import MessageEvent
    from nonebot.adapters.telegram.message import Entity
    from nonebot_plugin_saa import MessageFactory, SupportedAdapters, Text

    matcher = on_message()

    @matcher.handle()
    async def _(ev: MessageEvent):
        await MessageFactory(
            [Text(f"homo senpai {ev.message.extract_plain_text()}")]
        ).send(reply=True, at_sender=True)

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.telegram)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, config=BOT_CONFIG)

        msg_event = mock_telegram_message_event(Message("1919810"))
        ctx.receive_event(bot, msg_event)
        ctx.should_call_send(
            msg_event,
            Entity.mention("@homo_senpai ") + ("homo senpai 1919810"),
            None,
            reply_to_message_id=1145141919810,
        )

        msg_event = mock_telegram_message_event(Message("哼哼啊啊啊啊啊"), has_username=False)
        ctx.receive_event(bot, msg_event)
        ctx.should_call_send(
            msg_event,
            (
                Entity.text_link("homo senpai ", "tg://user?id=1145141919810")
                + ("homo senpai 哼哼啊啊啊啊啊")
            ),
            None,
            reply_to_message_id=1145141919810,
        )


async def test_send_active(app: App):
    from nonebot import get_driver
    from nonebot.adapters.telegram import Message
    from nonebot_plugin_saa import (
        MessageFactory,
        TargetTelegramCommon,
        TargetTelegramForum,
    )
    from nonebot_plugin_saa.adapters.telegram import build_fake_event

    async with app.test_api() as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.telegram)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, config=BOT_CONFIG)

        target_common = TargetTelegramCommon(chat_id=1145141919810)
        ctx.should_call_send(
            cast(Any, build_fake_event(target_common)),
            Message("114514"),
            None,
            reply_to_message_id=None,
        )
        await MessageFactory("114514").send_to(target_common, bot)

        target_forum = TargetTelegramForum(chat_id=114514, message_thread_id=1919810)
        ctx.should_call_send(
            cast(Any, build_fake_event(target_forum)),
            Message("1919810"),
            None,
            reply_to_message_id=None,
        )
        await MessageFactory("1919810").send_to(target_forum, bot)
