import pytest
from nonebug import App
from nonebot import get_driver
from nonebot.adapters.onebot.v11.bot import Bot
from nonebot.adapters.onebot.v11.message import MessageSegment

from nonebot_plugin_saa.registries import MessageId
from nonebot_plugin_saa.utils import SupportedAdapters
from nonebot_plugin_saa.abstract_factories import MessageSegmentFactory
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

    mtir = MessageFactory([t, i, r])
    assert mtir == MessageFactory([Text("abc"), i, r])

    mtirm = MessageFactory([t, i, r, m])
    assert len(mtirm) == 4

    # __add__
    assert t + "456" + t == MessageFactory([t, Text("456"), t])
    assert t + i == mti
    assert t + i + r + m == mtirm
    assert t + i + [r, m] == mtirm
    assert t + [i, r] + m == mtirm

    with pytest.raises(TypeError):
        t + 1  # type: ignore

    # __radd__
    assert "abc" + i == mti
    assert "abc" + i + r + m == mtirm
    assert "abc" + i + [r, m] == mtirm
    assert i.__radd__(t) == mti
    assert [t, i, r] + m == mtirm
    assert ["abc", i, r] + m == mtirm

    with pytest.raises(TypeError):
        1 + i  # type: ignore

    # __iadd__
    tt = Text("abc")
    tt += i
    assert tt == mti
    tt += [r, m]
    assert tt == mtirm

    mf = MessageFactory(t)

    assert ["456", i] + mf == MessageFactory(["456", i, t])

    with pytest.raises(TypeError):
        mf += 1  # type: ignore
    with pytest.raises(TypeError):
        mf += [1]  # type: ignore

    # __eq__
    assert t == Text("abc")
    assert t == "abc"
    assert not (t == 123)


def test_message_segment_saa_code():
    t = Text("abc")
    i = Image("123")
    r = Reply(MessageId(adapter_name=SupportedAdapters.onebot_v11))
    m = Mention("114514")

    def name_kvstr(ms: MessageSegmentFactory):
        kvstr = ",".join([f"{k}={v!r}" for k, v in ms.data.items()])
        return ms.__class__.__name__, kvstr

    def name_kvrepr(ms: MessageSegmentFactory):
        kvrepr = ", ".join([f"{k}={v!r}" for k, v in ms.data.items()])
        return ms.__class__.__name__, kvrepr

    assert str(t) == "abc"
    assert str(i) == "[SAA:{0}|{1}]".format(*name_kvstr(i))
    assert str(m) == "[SAA:{0}|{1}]".format(*name_kvstr(m))
    assert repr(t) == "{0}({1})".format(*name_kvrepr(t))
    assert repr(i) == "{0}({1})".format(*name_kvrepr(i))
    assert repr(m) == "{0}({1})".format(*name_kvrepr(m))

    r_kvstr = ",".join([f"{k}={v!r}" for k, v in r.data.dict().items()])
    assert str(r) == "[SAA:{0}|{1}]".format(r.__class__.__name__, r_kvstr)
    assert repr(r) == "{0}({1})".format(r.__class__.__name__, r_kvstr)


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
async def test_build_message(app: App):
    async with app.test_api() as ctx:
        adapter = get_driver()._adapters[str(SupportedAdapters.onebot_v11)]
        bot = ctx.create_bot(base=Bot, adapter=adapter, self_id="123")
        msg_factory = MessageFactory([Text("talk is cheap"), Text("show me the code")])
        with pytest.deprecated_call():
            msg = await msg_factory.build(bot)

        assert msg == MessageSegment.text("talk is cheap") + "show me the code"
