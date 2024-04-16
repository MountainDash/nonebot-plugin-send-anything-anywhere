import time
from functools import partial
from collections.abc import Awaitable
from typing import TYPE_CHECKING, Callable

import pytest
from nonebug import App
from nonebot.adapters.telegram import Bot
from nonebot.adapters.telegram.config import BotConfig

from .utils import assert_ms, mock_telegram_message_event

BOT_CONFIG = BotConfig(token="123456:ABC-DEF1234ghIkl-zyx57W2v1u123ew11")

if TYPE_CHECKING:
    from nonebot.adapters import MessageSegment

    from nonebot_plugin_saa import MessageSegmentFactory


AssertTelegramFuncType = Callable[
    [App, "MessageSegmentFactory", "MessageSegment"],
    Awaitable[bool],
]


@pytest.fixture
def assert_telegram(app: App):
    from nonebot_plugin_saa import SupportedAdapters

    return partial(
        assert_ms,
        Bot,
        SupportedAdapters.telegram,
        config=BOT_CONFIG,
    )


CHAT_ID = 1145141919810
USER_ID = 114514
MESSAGE_ID = 415411
THREAD_ID = 1919081
DATE = 1451441541
USERNAME = "homo_senpai"
FIRSTNAME = "homo"
LASTNAME = "senpai"
SEND_MESSAGE_PARAMS = {
    "chat_id": CHAT_ID,
    "message_thread_id": None,
    "entities": None,
    "reply_parameters": None,
    "disable_notification": None,
    "protect_content": None,
    "reply_to_message_id": None,
    "allow_sending_without_reply": None,
    "parse_mode": None,
    "link_preview_options": None,
    "reply_markup": None,
}
SEND_MEDIA_GROUP_PARAMS = {
    "chat_id": CHAT_ID,
    "message_thread_id": None,
    "media": [],
    "reply_parameters": None,
    "disable_notification": None,
    "protect_content": None,
    "reply_to_message_id": None,
    "allow_sending_without_reply": None,
}
DELETE_MESSAGE_PARAMS = {
    "chat_id": CHAT_ID,
    "message_id": MESSAGE_ID,
}

FAKE_MESSAGE_RETURN = {
    "message_id": MESSAGE_ID,
    "date": round(time.time() * 1000),
    "chat": {"id": CHAT_ID, "type": "private"},
}


async def test_text(app: App, assert_telegram: AssertTelegramFuncType):
    from nonebot.adapters.telegram.message import Entity

    from nonebot_plugin_saa import Text

    val = "114514"
    await assert_telegram(app, Text(val), Entity.text(val))


async def test_image(app: App, assert_telegram: AssertTelegramFuncType):
    from nonebot.adapters.telegram.message import File

    from nonebot_plugin_saa import Image

    val = "114514"
    await assert_telegram(app, Image(val), File.photo(val))


async def test_mention(app: App, assert_telegram: AssertTelegramFuncType):
    from nonebot.adapters.telegram.message import Entity

    from nonebot_plugin_saa import Mention

    await assert_telegram(app, Mention(f"@{USERNAME}"), Entity.mention(f"@{USERNAME} "))
    await assert_telegram(
        app,
        Mention(f"{USER_ID}"),
        Entity.text_link("用户 ", f"tg://user?id={USER_ID}"),
    )


async def test_mention_all(app: App, assert_telegram: AssertTelegramFuncType):
    from nonebot.adapters.telegram.message import Entity

    from nonebot_plugin_saa import MentionAll, SupportedAdapters

    await assert_telegram(app, MentionAll(), Entity.text("@everyone "))
    await assert_telegram(app, MentionAll(online_only=True), Entity.text("@online "))
    await assert_telegram(app, MentionAll("114514"), Entity.text("114514"))
    await assert_telegram(
        app, MentionAll(fallback="@1919810", online_only=True), Entity.text("@1919810")
    )

    ma = MentionAll()
    ma.set_special_fallback(SupportedAdapters.telegram, "1919810")
    await assert_telegram(app, ma, Entity.text("1919810"))


async def test_reply(app: App, assert_telegram: AssertTelegramFuncType):
    from nonebot.adapters.telegram.message import Reply as TGReply

    from nonebot_plugin_saa import Reply
    from nonebot_plugin_saa.adapters.telegram import TelegramMessageId

    await assert_telegram(
        app,
        Reply(TelegramMessageId(message_id=MESSAGE_ID, chat_id=CHAT_ID)),
        TGReply.reply(MESSAGE_ID, CHAT_ID),
    )


async def test_send(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.telegram import Bot, Message
    from nonebot.adapters.telegram.event import MessageEvent

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters

    message_rec = "114514"
    message_send_pfx = "homo senpai "

    matcher = on_message()

    @matcher.handle()
    async def _(ev: MessageEvent):
        await MessageFactory(
            [Text(f"{message_send_pfx}{ev.message.extract_plain_text()}")],
        ).send()

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.telegram)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, config=BOT_CONFIG)

        msg_event = mock_telegram_message_event(Message(message_rec))
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "send_message",
            {**SEND_MESSAGE_PARAMS, "text": f"{message_send_pfx}{message_rec}"},
            FAKE_MESSAGE_RETURN,
        )


async def test_extract_message_id(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.telegram.model import Chat
    from nonebot.adapters.telegram import Bot, Message
    from nonebot.adapters.telegram.event import MessageEvent
    from nonebot.adapters.telegram.model import Message as ModelMessage

    from nonebot_plugin_saa.registries import get_message_id
    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters
    from nonebot_plugin_saa.adapters.telegram import TelegramReceipt, TelegramMessageId

    message_rec = "114514"
    message_send_pfx = "homo senpai "
    message_id_recv = 114515
    message_id_send = 114516

    matcher = on_message()

    @matcher.handle()
    async def _(ev: MessageEvent):
        assert get_message_id(ev) == TelegramMessageId(
            message_id=message_id_recv,
            chat_id=CHAT_ID,
        )
        receipt = await MessageFactory(
            [Text(f"{message_send_pfx}{ev.message.extract_plain_text()}")],
        ).send()
        assert isinstance(receipt, TelegramReceipt)
        assert receipt.extract_message_id() == TelegramMessageId(
            message_id=message_id_send,
            chat_id=CHAT_ID,
        )

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.telegram)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, config=BOT_CONFIG)

        msg_event = mock_telegram_message_event(
            Message(message_rec),
            message_id=message_id_recv,
        )
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "send_message",
            {**SEND_MESSAGE_PARAMS, "text": f"{message_send_pfx}{message_rec}"},
            {**FAKE_MESSAGE_RETURN, "message_id": message_id_send},
        )

    mid1 = 111
    mid2 = 222
    mid3 = 333
    chat_type = "private"

    mm1 = ModelMessage(
        message_id=mid1,
        date=DATE,
        chat=Chat(id=CHAT_ID, type=chat_type),
    )
    mm2 = ModelMessage(
        message_id=mid2,
        date=DATE,
        chat=Chat(id=CHAT_ID, type=chat_type),
    )
    mm3 = ModelMessage(
        message_id=mid3,
        date=DATE,
        chat=Chat(id=CHAT_ID, type=chat_type),
    )
    receipt = TelegramReceipt(
        bot_id=f"{USER_ID}",
        chat_id=CHAT_ID,
        messages=[mm1, mm2, mm3],
    )
    assert receipt.extract_message_id() == TelegramMessageId(
        message_id=mid1,
        chat_id=CHAT_ID,
    )
    assert receipt.extract_message_id(0) == receipt.extract_message_id()
    assert receipt.extract_message_id(1) == TelegramMessageId(
        message_id=mid2,
        chat_id=CHAT_ID,
    )
    assert receipt.extract_message_id(2) == TelegramMessageId(
        message_id=mid3,
        chat_id=CHAT_ID,
    )
    with pytest.raises(IndexError):
        assert receipt.extract_message_id(4)


async def test_send_with_reply(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.telegram import Bot, Message
    from nonebot.adapters.telegram.event import MessageEvent
    from nonebot.adapters.telegram.model import MessageEntity, ReplyParameters

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters

    message_send_pfx = "sodayo "

    matcher = on_message()

    @matcher.handle()
    async def _(ev: MessageEvent):
        await MessageFactory(
            [Text(f"{message_send_pfx}{ev.message.extract_plain_text()}")],
        ).send(reply=True, at_sender=True)

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.telegram)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, config=BOT_CONFIG)

        msg_rec1 = "suki"
        msg_event = mock_telegram_message_event(Message(msg_rec1))
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "send_message",
            {
                **SEND_MESSAGE_PARAMS,
                "text": f"@{USERNAME} {message_send_pfx}{msg_rec1}",
                "entities": [
                    MessageEntity(type="mention", offset=0, length=len(USERNAME) + 2),
                ],
                "reply_parameters": ReplyParameters(
                    message_id=MESSAGE_ID,
                    chat_id=CHAT_ID,
                ),
            },
            FAKE_MESSAGE_RETURN,
        )

        msg_rec2 = "哼哼啊啊啊啊啊"
        msg_event = mock_telegram_message_event(Message(msg_rec2), has_username=False)
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "send_message",
            {
                **SEND_MESSAGE_PARAMS,
                "text": f"{FIRSTNAME} {LASTNAME} {message_send_pfx}{msg_rec2}",
                "entities": [
                    MessageEntity(
                        type="text_link",
                        offset=0,
                        length=len(FIRSTNAME) + len(LASTNAME) + 2,
                        url=f"tg://user?id={USER_ID}",
                    ),
                ],
                "reply_parameters": ReplyParameters(
                    message_id=MESSAGE_ID,
                    chat_id=CHAT_ID,
                ),
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

        msg1 = "114514"
        target_common = TargetTelegramCommon(chat_id=CHAT_ID)
        ctx.should_call_api(
            "send_message",
            {**SEND_MESSAGE_PARAMS, "text": msg1},
            FAKE_MESSAGE_RETURN,
        )
        await MessageFactory(msg1).send_to(target_common, bot)

        msg2 = "1919810"
        target_forum = TargetTelegramForum(chat_id=CHAT_ID, message_thread_id=THREAD_ID)
        ctx.should_call_api(
            "send_message",
            {
                **SEND_MESSAGE_PARAMS,
                "chat_id": CHAT_ID,
                "message_thread_id": THREAD_ID,
                "text": msg2,
            },
            FAKE_MESSAGE_RETURN,
        )
        await MessageFactory(msg2).send_to(target_forum, bot)


async def test_receipt(app: App):
    from nonebot import get_driver
    from nonebot.adapters.telegram import Bot
    from nonebot.adapters.telegram.model import InputMediaPhoto

    from nonebot_plugin_saa import (
        Image,
        MessageFactory,
        SupportedAdapters,
        TargetTelegramCommon,
    )

    async with app.test_api() as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.telegram)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, config=BOT_CONFIG)
        target_common = TargetTelegramCommon(chat_id=CHAT_ID)

        msg1 = "114514"
        ctx.should_call_api(
            "send_message",
            {**SEND_MESSAGE_PARAMS, "text": msg1},
            FAKE_MESSAGE_RETURN,
        )
        receipt = await MessageFactory(msg1).send_to(target_common, bot)

        ctx.should_call_api("delete_message", DELETE_MESSAGE_PARAMS, result=True)
        await receipt.revoke()

        media1 = "114514"
        media2 = "1919810"
        media_msg_id1 = 1145141919811
        media_msg_id2 = 1145141919812
        ctx.should_call_api(
            "send_media_group",
            {
                **SEND_MEDIA_GROUP_PARAMS,
                "media": [
                    InputMediaPhoto(media=media1),
                    InputMediaPhoto(media=media2),
                ],
            },
            [
                {**FAKE_MESSAGE_RETURN, "message_id": media_msg_id1},
                {**FAKE_MESSAGE_RETURN, "message_id": media_msg_id2},
            ],
        )
        receipt = await MessageFactory(
            [Image(media1), Image(media2)],
        ).send_to(target_common, bot)

        ctx.should_call_api(
            "delete_message",
            {**DELETE_MESSAGE_PARAMS, "message_id": media_msg_id1},
            result=True,
        )
        ctx.should_call_api(
            "delete_message",
            {**DELETE_MESSAGE_PARAMS, "message_id": media_msg_id2},
            result=True,
        )
        await receipt.revoke()
