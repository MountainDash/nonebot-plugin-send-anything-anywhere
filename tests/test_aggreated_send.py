from nonebug import App

from .utils import ob12_kwargs, mock_obv12_message_event


async def test_send(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.onebot.v12 import Bot, Message, PrivateMessageEvent

    from nonebot_plugin_saa import Text, SupportedAdapters, AggregatedMessageFactory

    matcher = on_message()

    @matcher.handle()
    async def process(msg: PrivateMessageEvent):
        await AggregatedMessageFactory([Text("123"), Text("456")]).send()

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.onebot_v12)]
        bot = ctx.create_bot(
            base=Bot,
            adapter=adapter_obj,
            **ob12_kwargs(platform="qqguild"),
            auto_connect=False,
        )
        msg_event = mock_obv12_message_event(Message("321"))
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "send_message",
            data={
                "message": Message("123"),
                "user_id": "2233",
                "detail_type": "private",
            },
            result=None,
        )
        ctx.should_call_api(
            "send_message",
            data={
                "message": Message("456"),
                "user_id": "2233",
                "detail_type": "private",
            },
            result=None,
        )


async def test_send_active(app: App):
    from nonebot import get_driver
    from nonebot.adapters.onebot.v12 import Bot, Message

    from nonebot_plugin_saa.utils.types import MessageFactory
    from nonebot_plugin_saa import (
        Text,
        TargetOB12Unknow,
        SupportedAdapters,
        AggregatedMessageFactory,
    )

    async with app.test_api() as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.onebot_v12)]
        bot = ctx.create_bot(
            base=Bot, adapter=adapter_obj, **ob12_kwargs(platform="banana")
        )
        ctx.should_call_api(
            "send_message",
            data={
                "message": Message("123"),
                "user_id": "2233",
                "group_id": None,
                "channel_id": None,
                "guild_id": None,
                "detail_type": "private",
            },
            result=None,
        )
        ctx.should_call_api(
            "send_message",
            data={
                "message": Message("456"),
                "user_id": "2233",
                "group_id": None,
                "channel_id": None,
                "guild_id": None,
                "detail_type": "private",
            },
            result=None,
        )
        target = TargetOB12Unknow(detail_type="private", user_id="2233")
        await AggregatedMessageFactory(
            [Text("123"), MessageFactory(Text("456"))]
        ).send_to(target, bot)
