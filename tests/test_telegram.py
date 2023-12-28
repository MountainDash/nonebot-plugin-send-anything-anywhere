import time
from functools import partial

import pytest
from nonebug import App
from nonebot.adapters.telegram import Bot
from nonebot.adapters.telegram.config import BotConfig

from .utils import assert_ms, mock_telegram_message_event

BOT_CONFIG = BotConfig(token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")


@pytest.fixture
def assert_telegram(app: App):
    from nonebot_plugin_saa import SupportedAdapters

    return partial(
        assert_ms,
        Bot,
        SupportedAdapters.telegram,
        config=BOT_CONFIG,
    )


SEND_MESSAGE_PARAMS = {
    "chat_id": 1145141919810,
    "message_thread_id": None,
    "text": "",
    "entities": None,
    "disable_notification": None,
    "protect_content": None,
    "reply_to_message_id": None,
    "allow_sending_without_reply": None,
    "parse_mode": None,
    "disable_web_page_preview": None,
    "reply_markup": None,
}
SEND_MEDIA_GROUP_PARAMS = {
    "chat_id": 1145141919810,
    "message_thread_id": None,
    "media": [],
    "disable_notification": None,
    "protect_content": None,
    "reply_to_message_id": None,
    "allow_sending_without_reply": None,
}
DELETE_MESSAGE_PARAMS = {
    "chat_id": 1145141919810,
    "message_id": 1145141919810,
}

FAKE_MESSAGE_RETURN = {
    "message_id": 1145141919810,
    "date": round(time.time() * 1000),
    "chat": {"id": 1145141919810, "type": "private"},
}


async def test_text(app: App, assert_telegram):
    from nonebot.adapters.telegram.message import Entity

    from nonebot_plugin_saa import Text

    await assert_telegram(app, Text("114514"), Entity.text("114514"))


async def test_image(app: App, assert_telegram):
    from nonebot.adapters.telegram.message import File

    from nonebot_plugin_saa import Image

    await assert_telegram(app, Image("114514"), File.photo("114514"))


async def test_mention(app: App, assert_telegram):
    from nonebot.adapters.telegram.message import Entity

    from nonebot_plugin_saa import Mention

    await assert_telegram(app, Mention("@senpai"), Entity.mention("@senpai "))

    await assert_telegram(
        app,
        Mention("114514"),
        Entity.text_link("用户 ", "tg://user?id=114514"),
    )


async def test_reply(app: App, assert_telegram):
    from nonebot.adapters.telegram.message import MessageSegment

    from nonebot_plugin_saa import Reply
    from nonebot_plugin_saa.adapters.telegram import TelegramMessageId

    await assert_telegram(
        app,
        Reply(TelegramMessageId(message_id=114514)),
        MessageSegment("reply", {"message_id": "114514"}),
    )


async def test_send(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.telegram import Bot, Message
    from nonebot.adapters.telegram.event import MessageEvent

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters

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
        ctx.should_call_api(
            "send_message",
            {**SEND_MESSAGE_PARAMS, "text": "homo senpai 114514"},
            FAKE_MESSAGE_RETURN,
        )


async def test_extract_message_id(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.telegram import Bot, Message
    from nonebot.adapters.telegram.event import MessageEvent

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters
    from nonebot_plugin_saa.adapters.telegram import TelegramReceipt, TelegramMessageId

    matcher = on_message()

    @matcher.handle()
    async def _(ev: MessageEvent):
        receipt = await MessageFactory(
            [Text(f"homo senpai {ev.message.extract_plain_text()}")]
        ).send()
        assert isinstance(receipt, TelegramReceipt)
        assert receipt.extract_message_id() == [
            TelegramMessageId(message_id=1145141919810)
        ]

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.telegram)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, config=BOT_CONFIG)

        msg_event = mock_telegram_message_event(Message("114514"))
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "send_message",
            {**SEND_MESSAGE_PARAMS, "text": "homo senpai 114514"},
            FAKE_MESSAGE_RETURN,
        )


async def test_send_with_reply(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.telegram import Bot, Message
    from nonebot.adapters.telegram.event import MessageEvent
    from nonebot.adapters.telegram.model import MessageEntity

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters

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
        ctx.should_call_api(
            "send_message",
            {
                **SEND_MESSAGE_PARAMS,
                "text": "@homo_senpai homo senpai 1919810",
                "entities": [MessageEntity(type="mention", offset=0, length=13)],
                "reply_to_message_id": 1145141919810,
            },
            FAKE_MESSAGE_RETURN,
        )

        msg_event = mock_telegram_message_event(Message("哼哼啊啊啊啊啊"), has_username=False)
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "send_message",
            {
                **SEND_MESSAGE_PARAMS,
                "text": "homo senpai homo senpai 哼哼啊啊啊啊啊",
                "entities": [
                    MessageEntity(
                        type="text_link",
                        offset=0,
                        length=12,
                        url="tg://user?id=1145141919810",
                    )
                ],
                "reply_to_message_id": 1145141919810,
            },
            FAKE_MESSAGE_RETURN,
        )


async def test_send_active(app: App):
    from nonebot import get_driver
    from nonebot.adapters.telegram import Bot

    from nonebot_plugin_saa import (
        MessageFactory,
        SupportedAdapters,
        TargetTelegramForum,
        TargetTelegramCommon,
    )

    async with app.test_api() as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.telegram)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, config=BOT_CONFIG)

        target_common = TargetTelegramCommon(chat_id=1145141919810)
        ctx.should_call_api(
            "send_message",
            {**SEND_MESSAGE_PARAMS, "text": "114514"},
            FAKE_MESSAGE_RETURN,
        )
        await MessageFactory("114514").send_to(target_common, bot)

        target_forum = TargetTelegramForum(chat_id=114514, message_thread_id=1919810)
        ctx.should_call_api(
            "send_message",
            {
                **SEND_MESSAGE_PARAMS,
                "chat_id": 114514,
                "message_thread_id": 1919810,
                "text": "1919810",
            },
            FAKE_MESSAGE_RETURN,
        )
        await MessageFactory("1919810").send_to(target_forum, bot)


async def test_receipt(app: App):
    from nonebot import get_driver
    from nonebot.adapters.telegram import Bot
    from nonebot.adapters.telegram.model import InputMedia

    from nonebot_plugin_saa import (
        Image,
        MessageFactory,
        SupportedAdapters,
        TargetTelegramCommon,
    )

    async with app.test_api() as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.telegram)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, config=BOT_CONFIG)
        target_common = TargetTelegramCommon(chat_id=1145141919810)

        ctx.should_call_api(
            "send_message",
            {**SEND_MESSAGE_PARAMS, "text": "114514"},
            FAKE_MESSAGE_RETURN,
        )
        receipt = await MessageFactory("114514").send_to(target_common, bot)

        ctx.should_call_api("delete_message", DELETE_MESSAGE_PARAMS, result=True)
        await receipt.revoke()

        ctx.should_call_api(
            "send_media_group",
            {
                **SEND_MEDIA_GROUP_PARAMS,
                "media": [
                    InputMedia(type="photo", media="114514"),
                    InputMedia(type="photo", media="1919810"),
                ],
            },
            [
                {**FAKE_MESSAGE_RETURN, "message_id": 1145141919811},
                {**FAKE_MESSAGE_RETURN, "message_id": 1145141919812},
            ],
        )
        receipt = await MessageFactory(
            [
                Image("114514"),
                Image("1919810"),
            ]
        ).send_to(target_common, bot)

        ctx.should_call_api(
            "delete_message",
            {**DELETE_MESSAGE_PARAMS, "message_id": 1145141919811},
            result=True,
        )
        ctx.should_call_api(
            "delete_message",
            {**DELETE_MESSAGE_PARAMS, "message_id": 1145141919812},
            result=True,
        )
        await receipt.revoke()
