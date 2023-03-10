from functools import partial

from nonebug import App
from nonebot.adapters.onebot.v11.bot import Bot

from nonebot_plugin_saa.utils import SupportedAdapters

from .utils import assert_ms, mock_obv11_message_event

assert_onebot_v11 = partial(assert_ms, Bot, SupportedAdapters.onebot_v11)


async def test_text(app: App):
    from nonebot.adapters.onebot.v11 import MessageSegment

    from nonebot_plugin_saa import Text

    await assert_onebot_v11(app, Text("123"), MessageSegment.text("123"))


async def test_image(app: App):
    from nonebot.adapters.onebot.v11 import MessageSegment

    from nonebot_plugin_saa import Image

    await assert_onebot_v11(app, Image("123"), MessageSegment.image("123"))


async def test_mention(app: App):
    from nonebot.adapters.onebot.v11 import MessageSegment

    from nonebot_plugin_saa import Mention

    await assert_onebot_v11(app, Mention("123"), MessageSegment.at("123"))


async def test_reply(app: App):
    from nonebot.adapters.onebot.v11 import MessageSegment

    from nonebot_plugin_saa import Reply

    await assert_onebot_v11(app, Reply(123), MessageSegment.reply(123))


async def test_send(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.onebot.v11 import Bot, Message, PrivateMessageEvent

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters

    matcher = on_message()

    @matcher.handle()
    async def process(msg: PrivateMessageEvent):
        await MessageFactory(Text("123")).send()

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.onebot_v11)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj)
        msg_event = mock_obv11_message_event(Message("321"))
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "send_msg",
            data={
                "message": Message("123"),
                "user_id": 2233,
                "message_type": "private",
            },
            result=None,
        )


async def test_send_with_reply(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.onebot.v11 import (
        Bot,
        Message,
        MessageSegment,
        PrivateMessageEvent,
    )

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters

    matcher = on_message()

    @matcher.handle()
    async def process(msg: PrivateMessageEvent):
        await MessageFactory(Text("123")).send(reply=True, at_sender=True)

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.onebot_v11)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj)
        msg_event = mock_obv11_message_event(Message("321"))
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "send_msg",
            data={
                "message": Message(
                    [
                        MessageSegment.reply(msg_event.message_id),
                        MessageSegment.at(msg_event.user_id),
                        MessageSegment.text("123"),
                    ]
                ),
                "user_id": 2233,
                "message_type": "private",
            },
            result=None,
        )


async def test_send_active(app: App):
    from nonebot import get_driver
    from nonebot.adapters.onebot.v11 import Message

    from nonebot_plugin_saa import TargetQQGroup, MessageFactory, TargetQQPrivate

    async with app.test_api() as ctx:
        adapter_ob11 = get_driver()._adapters[str(SupportedAdapters.onebot_v11)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_ob11)

        send_target_private = TargetQQPrivate(user_id=1122)
        ctx.should_call_api(
            "send_msg",
            data={
                "message": Message("123"),
                "user_id": 1122,
                "message_type": "private",
            },
            result=None,
        )
        await MessageFactory("123").send_to(bot, send_target_private)

        send_target_group = TargetQQGroup(group_id=1122)
        ctx.should_call_api(
            "send_msg",
            data={
                "message": Message("123"),
                "group_id": 1122,
                "message_type": "group",
            },
            result=None,
        )
        await MessageFactory("123").send_to(bot, send_target_group)
