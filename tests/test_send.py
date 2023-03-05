import pytest
from nonebug import App

from .utils import mock_obv11_message_event


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


async def test_not_send_in_handler(app: App):
    from nonebot_plugin_saa import Text, MessageFactory

    msg = MessageFactory(Text("123"))
    with pytest.raises(RuntimeError):
        await msg.send()
