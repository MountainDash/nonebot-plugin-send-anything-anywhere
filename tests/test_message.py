from nonebug import App
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.adapters.onebot.v11.message import MessageSegment

from nonebot_plugin_send_anything_anywhere import Text, MessageFactory
from nonebot_plugin_send_anything_anywhere.utils import SupportedAdapters

from .utils import make_fake_bot


def test_message_assamble():
    target_two_msg = MessageFactory([Text("abc"), Text("123")])

    assert len(target_two_msg) == 2
    assert target_two_msg[0] == Text("abc")
    assert target_two_msg[1] == Text("123")

    assert Text("abc") + "123" == target_two_msg
    assert "abc" + Text("123") == target_two_msg

    assert MessageFactory("abc") + "123" == target_two_msg
    assert "abc" + MessageFactory("123") == target_two_msg

    assert MessageFactory("abc").append("123") == target_two_msg


async def test_build_message(app: App):
    async with app.test_api() as ctx:
        bot = make_fake_bot(ctx, SupportedAdapters.onebot_v11, Bot, "123")
        msg_factory = MessageFactory([Text("talk is cheap"), Text("show me the code")])
        msg = await msg_factory.build(bot)

        assert msg == MessageSegment.text("talk is cheap") + "show me the code"
