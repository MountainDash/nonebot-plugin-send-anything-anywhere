import random
from typing import TYPE_CHECKING, Type

from nonebot import get_driver

if TYPE_CHECKING:
    from nonebug import App
    from nonebot.internal.adapter.bot import Bot
    from nonebot.internal.adapter.message import MessageSegment
    from nonebot.adapters.onebot.v11 import Message as OB11Message

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
