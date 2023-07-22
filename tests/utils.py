import random
from datetime import datetime
from typing import TYPE_CHECKING, Type, Literal, cast

from nonebot import get_driver

if TYPE_CHECKING:
    from nonebug import App
    from nonebot.internal.adapter.bot import Bot
    from nonebot.adapters.telegram import Message as TGMessage
    from nonebot.internal.adapter.message import MessageSegment
    from nonebot.adapters.onebot.v11 import Message as OB11Message
    from nonebot.adapters.onebot.v12 import Message as OB12Message
    from nonebot.adapters.qqguild import Message as QQGuildMessage
    from nonebot.adapters.telegram.event import MessageEvent as TGMessageEvent

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


def mock_obv11_poke_event(group=False):
    from nonebot.adapters.onebot.v11 import PokeNotifyEvent as OB11PokeNotifyEvent

    if not group:
        return OB11PokeNotifyEvent(
            time=1122,
            self_id=2233,
            post_type="notice",
            notice_type="notify",
            sub_type="poke",
            user_id=2233,
            target_id=2233,
        )
    else:
        return OB11PokeNotifyEvent(
            time=1122,
            self_id=2233,
            post_type="notice",
            notice_type="notify",
            sub_type="poke",
            user_id=2233,
            group_id=3344,
            target_id=2233,
        )


def mock_obv12_message_event(
    message: "OB12Message",
    detail_type: Literal[
        "private", "group", "channel", "qqguild_private", "qqguild_channel"
    ] = "private",
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
    elif detail_type == "channel":
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
    elif detail_type == "qqguild_private":
        return PrivateMessageEvent(
            id="1111",
            time=datetime.now(),
            type="message",
            detail_type="private",
            sub_type="",
            self=BotSelf(platform="qqguild", user_id="2233"),
            message_id=str(random.randrange(0, 10000)),
            message=message,
            original_message=message,
            alt_message=str(message),
            user_id="2233",
            qqguild={
                "guild_id": "4455",
                "src_guild_id": "5566",
            },
        )
    else:
        return ChannelMessageEvent(
            id="1111",
            time=datetime.now(),
            type="message",
            detail_type="channel",
            sub_type="",
            self=BotSelf(platform="qqguild", user_id="2233"),
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


def ob12_kwargs(platform="qq", impl="walle"):
    return {"platform": platform, "impl": impl}


def mock_telegram_message_event(
    message: "TGMessage",
    ev_type: Literal["private", "group", "forum", "channel"] = "private",
    has_username: bool = True,
) -> "TGMessageEvent":
    from nonebot.adapters.telegram.model import Chat, User
    from nonebot.adapters.telegram.event import (
        ChannelPostEvent,
        GroupMessageEvent,
        PrivateMessageEvent,
        ForumTopicMessageEvent,
    )

    chat_type = cast(
        Literal["private", "supergroup", "channel"],
        "supergroup" if ev_type in ["group", "forum"] else ev_type,
    )
    kwargs = {
        "message": message,
        "message_id": 1145141919810,
        "date": 1145141919810,
        "chat": Chat(id=1145141919810, type=chat_type),
        "from": User(
            id=1145141919810,
            is_bot=False,
            first_name="homo",
            last_name="senpai",
            username="homo_senpai" if has_username else None,
        ),
        "forward_from": None,
        "forward_from_chat": None,
        "forward_from_message_id": None,
        "forward_signature": None,
        "forward_sender_name": None,
        "forward_date": None,
        "via_bot": None,
        "has_protected_content": None,
        "media_group_id": None,
        "author_signature": None,
    }

    if ev_type == "channel":
        del kwargs["from"]
        return ChannelPostEvent(**kwargs)
    if ev_type == "forum":
        return ForumTopicMessageEvent(message_thread_id=1145141919810, **kwargs)
    if ev_type == "group":
        return GroupMessageEvent(**kwargs)
    return PrivateMessageEvent(**kwargs)
