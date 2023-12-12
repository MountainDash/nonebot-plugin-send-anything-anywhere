import pytest
from nonebug import App
from nonebot import get_driver
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.adapters.onebot.v11.message import MessageSegment

from nonebot_plugin_saa.registries import MessageId
from nonebot_plugin_saa.utils import SupportedAdapters
from nonebot_plugin_saa import Text, Image, Reply, Mention, MessageFactory


def test_message_assamble():
    target_two_msg = MessageFactory([Text("abc"), Text("123")])

    assert len(target_two_msg) == 2
    assert target_two_msg[0] == Text("abc")
    assert target_two_msg[1] == Text("123")

    assert Text("abc") + "123" == target_two_msg
    assert "abc" + Text("123") == target_two_msg

    assert MessageFactory("abc") + "123" == target_two_msg
    assert "abc" + MessageFactory("123") == target_two_msg

    assert MessageFactory("abc").append("123").append("456") == target_two_msg + Text(
        "456"
    )


def test_message_operation():
    empty_msg = MessageFactory()
    assert empty_msg == MessageFactory()
    assert empty_msg == MessageFactory([])
    assert empty_msg != MessageFactory("")

    empty_msg.append("abc")
    assert empty_msg == MessageFactory("abc")
    empty_msg.append(Text("456"))
    empty_msg.extend([Text("789"), Image("123")])
    assert empty_msg[0] == Text("abc")
    assert empty_msg[1] == Text("456")
    assert empty_msg[3] == Image("123")

    t = Text("abc")
    i = Image("123")
    r = Reply(MessageId(adapter_name=SupportedAdapters.onebot_v11))
    m = Mention("114514")

    mt = MessageFactory(t)
    assert mt == MessageFactory([t])
    assert mt == MessageFactory("abc")

    mti = MessageFactory([t, i])
    assert mti == MessageFactory(["abc", i])

    mtirm = MessageFactory([t, i, r, m])
    assert len(mtirm) == 4

    assert t + i == mti
    assert "abc" + i == mti
    assert t + i + r + m == mtirm
    assert "abc" + i + r + m == mtirm
    assert t + i + [r, m] == mtirm
    assert "abc" + i + [r, m] == mtirm
    assert [t, i, r] + m == mtirm
    assert ["abc", i, r] + m == mtirm
    t += i
    assert t == mti
    t += [r, m]
    assert t == mtirm


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
async def test_build_message(app: App):
    async with app.test_api() as ctx:
        adapter = get_driver()._adapters[str(SupportedAdapters.onebot_v11)]
        bot = ctx.create_bot(base=Bot, adapter=adapter, self_id="123")
        msg_factory = MessageFactory([Text("talk is cheap"), Text("show me the code")])
        with pytest.deprecated_call():
            msg = await msg_factory.build(bot)

        assert msg == MessageSegment.text("talk is cheap") + "show me the code"
