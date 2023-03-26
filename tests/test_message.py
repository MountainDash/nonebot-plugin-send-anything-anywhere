import pytest
from nonebug import App
from nonebot import get_driver
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.adapters.onebot.v11.message import MessageSegment


def test_message_assamble():
    from nonebot_plugin_saa import Text, MessageFactory

    target_two_msg = MessageFactory([Text("abc"), Text("123")])

    assert len(target_two_msg) == 2
    assert target_two_msg[0] == Text("abc")
    assert target_two_msg[1] == Text("123")

    assert Text("abc") + "123" == target_two_msg
    assert "abc" + Text("123") == target_two_msg

    assert MessageFactory("abc") + "123" == target_two_msg
    assert "abc" + MessageFactory("123") == target_two_msg

    assert MessageFactory("abc").append("123") == target_two_msg


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
async def test_build_message(app: App):
    from nonebot_plugin_saa import Text, MessageFactory
    from nonebot_plugin_saa.utils import SupportedAdapters

    async with app.test_api() as ctx:
        adapter = get_driver()._adapters[str(SupportedAdapters.onebot_v11)]
        bot = ctx.create_bot(base=Bot, adapter=adapter, self_id="123")
        msg_factory = MessageFactory([Text("talk is cheap"), Text("show me the code")])
        with pytest.deprecated_call():
            msg = await msg_factory.build(bot)

        assert msg == MessageSegment.text("talk is cheap") + "show me the code"
