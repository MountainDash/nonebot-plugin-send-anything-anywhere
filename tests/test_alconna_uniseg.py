from nonebug import App

from .utils import ob12_kwargs, mock_obv12_message_event


async def test_send(app: App):
    from nonebot_plugin_alconna import Text
    from nonebot import get_driver, on_message
    from nonebot.adapters.onebot.v12 import Bot, Message, PrivateMessageEvent

    from nonebot_plugin_saa import SupportedAdapters
    from nonebot_plugin_saa.ext.uniseg import UniMessageFactory

    matcher = on_message()

    @matcher.handle()
    async def process(msg: PrivateMessageEvent):
        await UniMessageFactory([Text("123"), Text("456")]).send()

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.onebot_v12)]
        bot = ctx.create_bot(
            base=Bot, adapter=adapter_obj, **ob12_kwargs(platform="qq")
        )
        msg_event = mock_obv12_message_event(Message("321"))
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "send_message",
            data={
                "message": Message("123456"),
                "user_id": "2233",
                "detail_type": "private",
            },
            result={"message_id": 12451},
        )
