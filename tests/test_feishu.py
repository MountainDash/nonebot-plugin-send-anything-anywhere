from io import BytesIO
from pathlib import Path
from functools import partial

import respx
import pytest
from nonebug import App
from httpx import Response
from nonebot import get_driver
from nonebot.compat import type_validate_python
from nonebot.adapters.feishu import Bot, Message
from nonebot.adapters.feishu.models import BotInfo
from nonebot.adapters.feishu.config import BotConfig

from .utils import assert_ms

BOT_CONFIG = BotConfig(app_id="114", app_secret="514", verification_token="1919810")
BOT_INFO = type_validate_python(
    BotInfo,
    {
        "activate_status": 2,
        "app_name": "name",
        "avatar_url": "https://s1-imfile.feishucdn.com/test.jpg",
        "ip_white_list": [],
        "open_id": "ou_123456",
    },
)
feishu_kwargs = {
    "self_id": "123456",
    "bot_config": BOT_CONFIG,
    "bot_info": BOT_INFO,
}


@pytest.fixture
def assert_feishu(app: App):
    from nonebot_plugin_saa import SupportedAdapters

    return partial(assert_ms, Bot, SupportedAdapters.feishu, **feishu_kwargs)


def mock_feishu_message_event(message: Message, group=False):
    from nonebot.adapters.feishu.models import (
        Sender,
        GroupEventMessage,
        PrivateEventMessage,
    )
    from nonebot.adapters.feishu import (
        UserId,
        EventHeader,
        GroupMessageEvent,
        PrivateMessageEvent,
        GroupMessageEventDetail,
        PrivateMessageEventDetail,
    )

    header = EventHeader(
        event_id="event_id",
        event_type="event_type",
        create_time="create_time",
        token="token",
        app_id="app_id",
        tenant_key="tenant_key",
        resource_id="resource_id",
        user_list=None,
    )
    sender = Sender(
        sender_id=UserId(
            open_id="open_id",
            user_id="user_id",
            union_id="union_id",
        ),
        tenant_key="tenant_key",
        sender_type="user",
    )
    msg_type, content = message.serialize()
    event_message_dict = {
        "message_id": "message_id",
        "root_id": "root_id",
        "parent_id": "parent_id",
        "create_time": "create_time",
        "chat_id": "chat_id",
        "message_type": msg_type,
        "content": content,
        "mentions": None,
    }

    if not group:
        return PrivateMessageEvent(
            schema="2.0",
            header=header,
            event=PrivateMessageEventDetail(
                sender=sender,
                message=PrivateEventMessage(chat_type="p2p", **event_message_dict),
            ),
            reply=None,
            _message=message,
            original_message=message,
        )
    else:
        return GroupMessageEvent(
            schema="2.0",
            header=header,
            event=GroupMessageEventDetail(
                sender=sender,
                message=GroupEventMessage(chat_type="group", **event_message_dict),
            ),
            reply=None,
            _message=message,
            original_message=message,
        )


async def test_text(app: App, assert_feishu):
    from nonebot.adapters.feishu import MessageSegment

    from nonebot_plugin_saa import Text

    await assert_feishu(app, Text("114514"), MessageSegment.text("114514"))


@respx.mock
async def test_image(app: App, tmp_path: Path):
    from nonebot.adapters.feishu import MessageSegment

    from nonebot_plugin_saa import Image, SupportedAdapters

    url = "https://nonebot.dev/logo.png"
    content = b"\x89PNG\r"
    image_route = respx.get(url)
    image_route.mock(return_value=Response(200, content=content))
    async with app.test_api() as ctx:
        adapter = get_driver()._adapters[str(SupportedAdapters.feishu)]
        bot = ctx.create_bot(base=Bot, adapter=adapter, **feishu_kwargs)

        ctx.should_call_api(
            "im/v1/images",
            {
                "method": "POST",
                "data": {"image_type": "message"},
                "files": {"image": ("file", content)},
            },
            {"code": 0, "msg": "success", "data": {"image_key": "114514"}},
        )
        generated_ms = await Image(url).build(bot)
        assert generated_ms == MessageSegment.image("114514")

        ctx.should_call_api(
            "im/v1/images",
            {
                "method": "POST",
                "data": {"image_type": "message"},
                "files": {"image": ("file", content)},
            },
            {"code": 0, "msg": "success", "data": {"image_key": "114514"}},
        )
        generated_ms = await Image(content).build(bot)
        assert generated_ms == MessageSegment.image("114514")

        image_path = tmp_path / "test.png"
        with image_path.open("wb") as f:
            f.write(content)
        ctx.should_call_api(
            "im/v1/images",
            {
                "method": "POST",
                "data": {"image_type": "message"},
                "files": {"image": ("file", content)},
            },
            {"code": 0, "msg": "success", "data": {"image_key": "114514"}},
        )
        generated_ms = await Image(image_path).build(bot)
        assert generated_ms == MessageSegment.image("114514")

        ctx.should_call_api(
            "im/v1/images",
            {
                "method": "POST",
                "data": {"image_type": "message"},
                "files": {"image": ("file", content)},
            },
            {"code": 0, "msg": "success", "data": {"image_key": "114514"}},
        )
        generated_ms = await Image(BytesIO(content)).build(bot)
        assert generated_ms == MessageSegment.image("114514")


async def test_mention(app: App, assert_feishu):
    from nonebot.adapters.feishu.message import At

    from nonebot_plugin_saa import Mention

    await assert_feishu(app, Mention("114514"), At("at", {"user_id": "114514"}))


async def test_reply(app: App, assert_feishu):
    from nonebot.adapters.feishu import MessageSegment

    from nonebot_plugin_saa import Reply
    from nonebot_plugin_saa.adapters.feishu import FeishuMessageId

    await assert_feishu(
        app,
        Reply(FeishuMessageId(message_id="114514")),
        MessageSegment("reply", {"message_id": "114514"}),
    )


async def test_send(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.feishu import Bot, Message, MessageEvent, MessageSegment

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters

    matcher = on_message()

    @matcher.handle()
    async def _(event: MessageEvent):
        await MessageFactory([Text("1919810")]).send()

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.feishu)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **feishu_kwargs)

        msg_event = mock_feishu_message_event(Message("114514"))
        msg_type, content = Message([MessageSegment.text("1919810")]).serialize()
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "im/v1/messages",
            {
                "method": "POST",
                "query": {"receive_id_type": "open_id"},
                "body": {
                    "receive_id": "open_id",
                    "content": content,
                    "msg_type": msg_type,
                },
            },
            {"code": 0, "msg": "success", "data": {"message_id": "114514"}},
        )


async def test_extract_message_id(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.feishu import Bot, Message, MessageEvent, MessageSegment

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters
    from nonebot_plugin_saa.adapters.feishu import FeishuReceipt, FeishuMessageId

    matcher = on_message()

    @matcher.handle()
    async def _(event: MessageEvent):
        receipt = await MessageFactory([Text("1919810")]).send()
        assert isinstance(receipt, FeishuReceipt)
        assert receipt.extract_message_id() == FeishuMessageId(message_id="114514")

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.feishu)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **feishu_kwargs)

        msg_event = mock_feishu_message_event(Message("114514"))
        msg_type, content = Message([MessageSegment.text("1919810")]).serialize()
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "im/v1/messages",
            {
                "method": "POST",
                "query": {"receive_id_type": "open_id"},
                "body": {
                    "receive_id": "open_id",
                    "content": content,
                    "msg_type": msg_type,
                },
            },
            {"code": 0, "msg": "success", "data": {"message_id": "114514"}},
        )


async def test_send_revoke(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.feishu import Bot, Message, MessageEvent, MessageSegment

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters

    matcher = on_message()

    @matcher.handle()
    async def _(event: MessageEvent):
        receipt = await MessageFactory([Text("1919810")]).send()
        await receipt.revoke()

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.feishu)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **feishu_kwargs)

        msg_event = mock_feishu_message_event(Message("114514"))
        msg_type, content = Message([MessageSegment.text("1919810")]).serialize()
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "im/v1/messages",
            {
                "method": "POST",
                "query": {"receive_id_type": "open_id"},
                "body": {
                    "receive_id": "open_id",
                    "content": content,
                    "msg_type": msg_type,
                },
            },
            {"code": 0, "msg": "success", "data": {"message_id": "114514"}},
        )
        ctx.should_call_api("im/v1/messages/114514", {"method": "DELETE"}, {})


async def test_send_with_reply_and_revoke(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.feishu.message import At
    from nonebot.adapters.feishu import Bot, Message, MessageEvent, MessageSegment

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters

    matcher = on_message()

    @matcher.handle()
    async def _(event: MessageEvent):
        receipt = await MessageFactory([Text("1919810")]).send(
            reply=True, at_sender=True
        )
        await receipt.revoke()

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.feishu)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **feishu_kwargs)

        msg_event = mock_feishu_message_event(Message("114514"), group=True)
        msg_type, content = Message(
            [At("at", {"user_id": "open_id"}), MessageSegment.text("1919810")]
        ).serialize()
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "im/v1/messages/message_id/reply",
            {"method": "POST", "body": {"content": content, "msg_type": msg_type}},
            {"code": 0, "msg": "success", "data": {"message_id": "114514"}},
        )
        ctx.should_call_api("im/v1/messages/114514", {"method": "DELETE"}, {})


async def test_send_active(app: App):
    from nonebot import get_driver
    from nonebot.adapters.feishu import Bot, Message, MessageSegment

    from nonebot_plugin_saa import (
        MessageFactory,
        SupportedAdapters,
        TargetFeishuGroup,
        TargetFeishuPrivate,
    )

    async with app.test_api() as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.feishu)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **feishu_kwargs)

        msg_type, content = Message([MessageSegment.text("114514")]).serialize()

        target_private = TargetFeishuPrivate(open_id="open_id")
        ctx.should_call_api(
            "im/v1/messages",
            {
                "method": "POST",
                "query": {"receive_id_type": "open_id"},
                "body": {
                    "receive_id": "open_id",
                    "content": content,
                    "msg_type": msg_type,
                },
            },
            {"code": 0, "msg": "success", "data": {"message_id": "114514"}},
        )
        await MessageFactory("114514").send_to(target_private, bot)

        target_group = TargetFeishuGroup(chat_id="chat_id")
        ctx.should_call_api(
            "im/v1/messages",
            {
                "method": "POST",
                "query": {"receive_id_type": "chat_id"},
                "body": {
                    "receive_id": "chat_id",
                    "content": content,
                    "msg_type": msg_type,
                },
            },
            {"code": 0, "msg": "success", "data": {"message_id": "114514"}},
        )
        await MessageFactory("114514").send_to(target_group, bot)
