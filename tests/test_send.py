import pytest

pytest.importorskip("nonebot.adapters.onebot")
from nonebug import App
from nonebot import get_driver, on_message

from tests.utils import ob12_kwargs, mock_obv12_message_event


async def test_not_send_in_handler(app: App):
    from nonebot_plugin_saa import Text, MessageFactory

    msg = MessageFactory(Text("123"))
    with pytest.raises(RuntimeError):
        await msg.send()


async def test_send_message(app: App):
    from nonebot.adapters.onebot.v12 import Bot, Message

    from nonebot_plugin_saa import (
        Text,
        MessageFactory,
        SupportedAdapters,
        AggregatedMessageFactory,
    )

    for test_subject in [
        MessageFactory("123"),
        Text("123"),
        AggregatedMessageFactory([MessageFactory("123")]),
    ]:
        for method_to_call, args, assertion in [
            ("finish", (), lambda ctx: ctx.should_finished()),
            ("pause", (), lambda ctx: ctx.should_paused()),
            ("reject", (), lambda ctx: ctx.should_rejected()),
            ("reject_arg", ("11",), lambda ctx: ctx.should_rejected()),
            ("reject_receive", ("11",), lambda ctx: ctx.should_rejected()),
        ]:
            matcher = on_message()

            @matcher.handle()
            async def test_matcher():
                await getattr(test_subject, method_to_call)(*args)

            async with app.test_matcher(matcher) as ctx:
                ob12_adapter = get_driver()._adapters[str(SupportedAdapters.onebot_v12)]
                bot = ctx.create_bot(base=Bot, adapter=ob12_adapter, **ob12_kwargs())
                event = mock_obv12_message_event(Message("123"))
                ctx.receive_event(bot, event)
                ctx.should_call_api(
                    "send_message",
                    data={
                        "message": Message("123"),
                        "detail_type": "private",
                        "user_id": event.user_id,
                    },
                    result={"message_id": "12451"},
                )
                assertion(ctx)
