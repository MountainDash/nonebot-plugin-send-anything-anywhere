from functools import partial

from nonebug import App
from nonebot.adapters.feishu.bot import BotInfo
from nonebot.adapters.feishu import Bot, Message
from nonebot.adapters.feishu.config import BotConfig

from nonebot_plugin_saa.utils import SupportedAdapters

from .utils import assert_ms

BOT_CONFIG = BotConfig(app_id="114", app_secret="514", verification_token="1919810")
BOT_INFO = BotInfo.parse_obj(
    {
        "activate_status": 2,
        "app_name": "name",
        "avatar_url": "https://s1-imfile.feishucdn.com/test.jpg",
        "ip_white_list": [],
        "open_id": "ou_123456",
    }
)
create_bot_kwargs = {"bot_config": BOT_CONFIG, "bot_info": BOT_INFO}
assert_feishu = partial(assert_ms, Bot, SupportedAdapters.feishu, **create_bot_kwargs)


def mock_feishu_message_event(message: Message, group=False):
    from nonebot.adapters.feishu import (
        Sender,
        UserId,
        EventHeader,
        GroupEventMessage,
        GroupMessageEvent,
        PrivateEventMessage,
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
    event_message_dict = {
        "message_id": "message_id",
        "root_id": "root_id",
        "parent_id": "parent_id",
        "create_time": "create_time",
        "chat_id": "chat_id",
        "chat_type": "p2p",
        "message_type": "message_type",
        "mentions": None,
    }

    if not group:
        return PrivateMessageEvent(
            schema="2.0",
            header=header,
            event=PrivateMessageEventDetail(
                sender=sender,
                message=PrivateEventMessage(
                    chat_type="p2p", content=message, **event_message_dict
                ),
            ),
            reply=None,
        )
    else:
        return GroupMessageEvent(
            schema="2.0",
            header=header,
            event=GroupMessageEventDetail(
                sender=sender,
                message=GroupEventMessage(
                    chat_type="group", content=message, **event_message_dict
                ),
            ),
            reply=None,
        )


async def test_text(app: App):
    from nonebot.adapters.feishu import MessageSegment

    from nonebot_plugin_saa import Text

    await assert_feishu(app, Text("114514"), MessageSegment.text("114514"))


async def test_image(app: App):
    from nonebot.adapters.feishu import MessageSegment

    from nonebot_plugin_saa import Image

    await assert_feishu(app, Image("114514"), MessageSegment.image("114514"))


async def test_mention(app: App):
    from nonebot.adapters.feishu import MessageSegment

    from nonebot_plugin_saa import Mention

    await assert_feishu(app, Mention("114514"), MessageSegment.at("114514"))


async def test_reply(app: App):
    from nonebot.adapters.feishu import MessageSegment

    from nonebot_plugin_saa import Reply

    await assert_feishu(
        app,
        Reply(114514),
        MessageSegment("reply", {"message_id": "114514"}),
    )


async def test_send(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.feishu import (
        Bot,
        Message,
        MessageEvent,
        MessageSegment,
        MessageSerializer,
    )

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters

    matcher = on_message()

    @matcher.handle()
    async def _(event: MessageEvent):
        await MessageFactory([Text("1919810")]).send()

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.feishu)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **create_bot_kwargs)

        msg_event = mock_feishu_message_event(Message("114514"))
        msg_type, content = MessageSerializer(
            Message([MessageSegment.text("1919810")])
        ).serialize()
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
            {},
        )


async def test_send_with_reply(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.feishu import (
        Bot,
        Message,
        MessageEvent,
        MessageSegment,
        MessageSerializer,
    )

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters

    matcher = on_message()

    @matcher.handle()
    async def _(event: MessageEvent):
        await MessageFactory([Text("1919810")]).send(reply=True, at_sender=True)

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.feishu)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **create_bot_kwargs)

        msg_event = mock_feishu_message_event(Message("114514"))
        msg_type, content = MessageSerializer(
            Message([MessageSegment.at("open_id"), MessageSegment.text("1919810")])
        ).serialize()
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "im/v1/messages/message_id/reply",
            {"method": "POST", "body": {"content": content, "msg_type": msg_type}},
            {},
        )


async def test_send_active(app: App):
    from nonebot import get_driver
    from nonebot.adapters.feishu import Bot, Message, MessageSegment, MessageSerializer

    from nonebot_plugin_saa import (
        MessageFactory,
        SupportedAdapters,
        TargetFeishuGroup,
        TargetFeishuPrivate,
    )

    async with app.test_api() as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.feishu)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **create_bot_kwargs)

        msg_type, content = MessageSerializer(
            Message([MessageSegment.text("114514")])
        ).serialize()

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
            {},
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
            {},
        )
        await MessageFactory("114514").send_to(target_group, bot)
