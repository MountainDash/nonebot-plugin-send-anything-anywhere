from functools import partial

from nonebug import App
from nonebot.adapters.telegram import Bot
from nonebot.adapters.telegram.config import BotConfig

from nonebot_plugin_saa.utils import SupportedAdapters

from .utils import assert_ms, mock_telegram_message_event

assert_telegram = partial(
    assert_ms,
    Bot,
    SupportedAdapters.telegram,
    config=BotConfig(token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11"),
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

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters

    matcher = on_message()

    @matcher.handle()
    async def process():
        await MessageFactory(Text("114514")).send()

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.telegram)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj)
        msg_event = mock_telegram_message_event(Message("114514"))
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "sendMessage",
            data={
                "text": "114514",
                "chat_id": 1145141919810,
            },
            result=None,
        )


async def test_send_with_reply(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.telegram import Bot, Message

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters

    matcher = on_message()

    @matcher.handle()
    async def process():
        await MessageFactory(Text("114514")).send(reply=True, at_sender=True)

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.telegram)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj)
        msg_event = mock_telegram_message_event(Message("114514"))
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "sendMessage",
            data={
                "text": "114514",
                "chat_id": 1145141919810,
                "reply_to_message_id": 1145141919810,
            },
            result=None,
        )


async def test_send_active(app: App):
    from nonebot import get_driver

    from nonebot_plugin_saa import (
        MessageFactory,
        TargetTelegramForum,
        TargetTelegramCommon,
    )

    async with app.test_api() as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.telegram)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj)

        target_common = TargetTelegramCommon(chat_id=1145141919810)
        ctx.should_call_api(
            "sendMessage",
            data={
                "text": "114514",
                "chat_id": 1145141919810,
            },
            result=None,
        )
        await MessageFactory("114514").send_to(target_common, bot)

        target_forum = TargetTelegramForum(chat_id=114514, message_thread_id=1919810)
        ctx.should_call_api(
            "sendMessage",
            data={
                "text": "114514",
                "chat_id": 114514,
                "message_thread_id": 1919810,
            },
            result=None,
        )
        await MessageFactory("114514").send_to(target_forum, bot)
