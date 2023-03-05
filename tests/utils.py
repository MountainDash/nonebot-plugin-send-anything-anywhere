import random
from datetime import datetime
from typing import TYPE_CHECKING, Type, Literal

from nonebot import get_driver

if TYPE_CHECKING:
    from nonebug import App
    from nonebot.internal.adapter.bot import Bot
    from nonebot.internal.adapter.message import MessageSegment
    from nonebot.adapters.onebot.v11 import Message as OB11Message
    from nonebot.adapters.onebot.v12 import Message as OB12Message
    from nonebot.adapters.qqguild import Message as QQGuildMessage

    from nonebot_plugin_saa.utils import SupportedAdapters, MessageSegmentFactory


async def assert_ms(
    bot_base: "Type[Bot]",
    adapter: "SupportedAdapters",
    app: "App",
    ms_factory: "MessageSegmentFactory",
    ms: "MessageSegment",
    **kwargs,
):
    if not kwargs:
        kwargs["self_id"] = "314159"

    async with app.test_api() as ctx:
        adapter_obj = get_driver()._adapters[str(adapter)]
        bot = ctx.create_bot(base=bot_base, adapter=adapter_obj, **kwargs)
        generated_ms = await ms_factory.build(bot)
        assert generated_ms.data == ms.data


def mock_obv11_message_event(message: "OB11Message", group=False):
    from nonebot.adapters.onebot.v11.event import Sender
    from nonebot.adapters.onebot.v11 import GroupMessageEvent as OB11GroupMessageEvent
    from nonebot.adapters.onebot.v11 import (
        PrivateMessageEvent as OB11PrivateMessageEvent,
    )

    if not group:
        return OB11PrivateMessageEvent(
            time=1122,
            self_id=2233,
            post_type="message",
            sub_type="",
            user_id=2233,
            message_type="private",
            message_id=random.randrange(0, 10000),
            message=message,
            original_message=message,
            raw_message=str(message),
            font=1,
            sender=Sender(user_id=2233),
            to_me=False,
        )
    else:
        return OB11GroupMessageEvent(
            time=1122,
            self_id=2233,
            group_id=3344,
            post_type="message",
            sub_type="",
            user_id=2233,
            message_type="group",
            message_id=random.randrange(0, 10000),
            message=message,
            original_message=message,
            raw_message=str(message),
            font=1,
            sender=Sender(user_id=2233),
            to_me=False,
        )


def mock_obv12_message_event(
    message: "OB12Message",
    detail_type: Literal["private", "group", "channel"] = "private",
):
    from nonebot.adapters.onebot.v12.event import BotSelf
    from nonebot.adapters.onebot.v12 import (
        GroupMessageEvent,
        ChannelMessageEvent,
        PrivateMessageEvent,
    )

    if detail_type == "private":
        return PrivateMessageEvent(
            id=str(random.randint(0, 10000)),
            time=datetime.now(),
            type="message",
            detail_type="private",
            sub_type="",
            self=BotSelf(platform="qq", user_id="2233"),
            message_id=str(random.randrange(0, 10000)),
            message=message,
            original_message=message,
            alt_message=str(message),
            user_id="2233",
        )
    elif detail_type == "group":
        return GroupMessageEvent(
            id=str(random.randint(0, 10000)),
            time=datetime.now(),
            type="message",
            detail_type="group",
            sub_type="",
            self=BotSelf(platform="qq", user_id="2233"),
            message_id=str(random.randrange(0, 10000)),
            message=message,
            original_message=message,
            alt_message=str(message),
            user_id="2233",
            group_id="4455",
        )
    else:
        return ChannelMessageEvent(
            id=str(random.randint(0, 10000)),
            time=datetime.now(),
            type="message",
            detail_type="channel",
            sub_type="",
            self=BotSelf(platform="qq", user_id="2233"),
            message_id=str(random.randrange(0, 10000)),
            message=message,
            original_message=message,
            alt_message=str(message),
            user_id="2233",
            guild_id="5566",
            channel_id="6677",
        )


def mock_qqguild_message_event(message: "QQGuildMessage", direct=False):
    from nonebot.adapters.qqguild.api.model import User
    from nonebot.adapters.qqguild.event import EventType
    from nonebot.adapters.qqguild import MessageCreateEvent, DirectMessageCreateEvent

    if not direct:
        return MessageCreateEvent(
            __type__=EventType.MESSAGE_CREATE,
            id=str(random.randrange(0, 10000)),
            guild_id=1122,
            channel_id=2233,
            content=message.extract_content(),
            author=User(id=3344),
        )
    else:
        return DirectMessageCreateEvent(
            __type__=EventType.DIRECT_MESSAGE_CREATE,
            id=str(random.randrange(0, 10000)),
            guild_id=1122,
            channel_id=2233,
            content=message.extract_content(),
            author=User(id=3344),
        )
