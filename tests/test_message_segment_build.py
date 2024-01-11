import pytest
from nonebug import App

from .utils import assert_ms, mock_obv11_message_event


@pytest.fixture(scope="module")
def MyText():
    from nonebot_plugin_saa.abstract_factories import MessageSegmentFactory

    class MyText(MessageSegmentFactory):
        text: str

        def __init__(self, text: str) -> None:
            self.text = text
            super().__init__()

    return MyText


@pytest.fixture
def dummy_factory(app: App, MyText):
    class _Test(MyText):
        pass

    return _Test


@pytest.fixture
def onebot_v11(app: App, MyText):
    from nonebot_plugin_saa.utils import SupportedAdapters

    return SupportedAdapters.onebot_v11


async def test_sync_without_bot(app: App, dummy_factory, onebot_v11):
    from nonebot.adapters.onebot.v11.bot import Bot
    from nonebot.adapters.onebot.v11.message import MessageSegment

    from nonebot_plugin_saa import SupportedAdapters
    from nonebot_plugin_saa.abstract_factories import register_ms_adapter

    @register_ms_adapter(onebot_v11, dummy_factory)
    def _text(t):
        return MessageSegment.text("314159")

    await assert_ms(
        Bot,
        SupportedAdapters.onebot_v11,
        app,
        dummy_factory("314159"),
        MessageSegment.text("314159"),
    )


async def test_sync_with_bot(app: App, dummy_factory, onebot_v11):
    from nonebot.adapters.onebot.v11.bot import Bot
    from nonebot.adapters.onebot.v11.message import MessageSegment

    from nonebot_plugin_saa import SupportedAdapters
    from nonebot_plugin_saa.abstract_factories import register_ms_adapter

    @register_ms_adapter(onebot_v11, dummy_factory)
    def _text(t, bot):
        return MessageSegment.text("314159")

    await assert_ms(
        Bot,
        SupportedAdapters.onebot_v11,
        app,
        dummy_factory("314159"),
        MessageSegment.text("314159"),
    )


async def test_async_without_bot(app: App, dummy_factory, onebot_v11):
    from nonebot.adapters.onebot.v11.bot import Bot
    from nonebot.adapters.onebot.v11.message import MessageSegment

    from nonebot_plugin_saa import SupportedAdapters
    from nonebot_plugin_saa.abstract_factories import register_ms_adapter

    @register_ms_adapter(onebot_v11, dummy_factory)
    async def _text(t):
        return MessageSegment.text("314159")

    await assert_ms(
        Bot,
        SupportedAdapters.onebot_v11,
        app,
        dummy_factory("314159"),
        MessageSegment.text("314159"),
    )


async def test_async_with_bot(app: App, dummy_factory, onebot_v11):
    from nonebot.adapters.onebot.v11.bot import Bot
    from nonebot.adapters.onebot.v11.message import MessageSegment

    from nonebot_plugin_saa import SupportedAdapters
    from nonebot_plugin_saa.abstract_factories import register_ms_adapter

    @register_ms_adapter(onebot_v11, dummy_factory)
    async def _text(t, bot):
        return MessageSegment.text("314159")

    await assert_ms(
        Bot,
        SupportedAdapters.onebot_v11,
        app,
        dummy_factory("314159"),
        MessageSegment.text("314159"),
    )


async def test_send_with_reply(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.onebot.v11 import (
        Bot,
        Message,
        MessageSegment,
        PrivateMessageEvent,
    )

    from nonebot_plugin_saa import Text, SupportedAdapters

    matcher = on_message()

    @matcher.handle()
    async def process(msg: PrivateMessageEvent):
        await Text("123").send(reply=True, at_sender=True)

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
            result={"message_id": 12451},
        )


async def test_send_active(app: App):
    from nonebot import get_driver
    from nonebot.adapters.onebot.v11 import Bot, Message

    from nonebot_plugin_saa import Text, TargetQQPrivate, SupportedAdapters

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
            result={"message_id": 12451},
        )
        await Text("123").send_to(send_target_private, bot)
