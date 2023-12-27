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

    assert MessageFactory("abc").append("123") == target_two_msg


@pytest.mark.filterwarnings("ignore::DeprecationWarning")
async def test_build_message(app: App):
    async with app.test_api() as ctx:
        adapter = get_driver()._adapters[str(SupportedAdapters.onebot_v11)]
        bot = ctx.create_bot(base=Bot, adapter=adapter, self_id="123")
        msg_factory = MessageFactory([Text("talk is cheap"), Text("show me the code")])
        with pytest.deprecated_call():
            msg = await msg_factory.build(bot)

        assert msg == MessageSegment.text("talk is cheap") + "show me the code"


def test_message_add(app: App):
    s = "123"
    t = Text("abc")
    i = Image("http://example.com/abc.png")
    r = Reply(MessageId(adapter_name=SupportedAdapters.fake))
    m = Mention("123")

    assert t == "abc"
    assert t != "123"
    assert t == Text("abc")
    assert t != Text("123")
    assert t != i
    assert t != r
    assert t != m
    st = s + t
    assert st == MessageFactory([Text("123"), Text("abc")])
    tt = t + t
    assert tt == MessageFactory([Text("abc"), Text("abc")])
    ts = t + s
    assert ts == MessageFactory([Text("abc"), Text("123")])
    assert ts == MessageFactory([t, s])

    si = s + i
    assert si == MessageFactory([Text("123"), Image("http://example.com/abc.png")])

    is_ = i + s
    assert is_ == MessageFactory([Image("http://example.com/abc.png"), Text("123")])

    ti = t + i
    assert ti == MessageFactory([Text("abc"), Image("http://example.com/abc.png")])

    it = i + t
    assert it == MessageFactory([Image("http://example.com/abc.png"), Text("abc")])

    sit = s + i + t
    assert sit == MessageFactory(
        [Text("123"), Image("http://example.com/abc.png"), Text("abc")]
    )
    assert sit == MessageFactory([s, i, t])
    assert sit == [s, i] + t

    tit = t + i + t
    t_it = t + [i, t]
    assert tit == MessageFactory(
        [Text("abc"), Image("http://example.com/abc.png"), Text("abc")]
    )
    assert tit == MessageFactory([t, i, t])
    assert tit == t_it

    tir = t + i + r
    assert tir == t + [i, r]
    assert tir == MessageFactory([t, i, r])
    ir = i + r
    assert ti + r == t + ir

    tt_iadd = Text("q")
    tt_iadd += t
    assert tt_iadd == MessageFactory([Text("q"), t])


def test_segment_data():
    assert len(Text("text")) == 4
    assert Text("text").get("data") == {"text": "text"}
    assert list(Text("text").keys()) == ["type", "data"]
    assert list(Text("text").values()) == ["text", {"text": "text"}]
    assert list(Text("text").items()) == [
        ("type", "text"),
        ("data", {"text": "text"}),
    ]


def test_segment_join():
    seg = Text("test")
    iterable = [
        Text("first"),
        MessageFactory([Text("second"), Text("third")]),
    ]

    assert seg.join(iterable) == MessageFactory(
        [
            Text("first"),
            Text("test"),
            Text("second"),
            Text("third"),
        ]
    )


def test_segment_copy():
    origin = Text("text")
    copy = origin.copy()
    assert origin is not copy
    assert origin == copy


def test_message_getitem():
    message = MessageFactory(
        [
            Text("test"),
            Image("test2"),
            Image("test3"),
            Text("test4"),
        ]
    )

    assert message[0] == Text("test")

    assert message[:2] == MessageFactory([Text("test"), Image("test2")])

    assert message["image"] == MessageFactory([Image("test2"), Image("test3")])

    assert message["image", 0] == Image("test2")
    assert message["image", 0:2] == message["image"]

    assert message.index(message[0]) == 0
    assert message.index("image") == 1

    assert message.get("image") == message["image"]
    assert message.get("image", 114514) == message["image"]
    assert message.get("image", 1) == MessageFactory([message["image", 0]])

    assert message.count("image") == 2


def test_message_contains():
    message = MessageFactory(
        [
            Text("test"),
            Image("test2"),
            Image("test3"),
            Text("test4"),
        ]
    )

    assert message.has(Text("test")) is True
    assert Text("test") in message
    assert message.has("image") is True
    assert "image" in message

    assert message.has(Text("foo")) is False
    assert Text("foo") not in message
    assert message.has("foo") is False
    assert "foo" not in message


def test_message_only():
    message = MessageFactory(
        [
            Text("test"),
            Text("test2"),
        ]
    )

    assert message.only("text") is True
    assert message.only(Text("test")) is False

    message = MessageFactory(
        [
            Text("test"),
            Image("test2"),
            Image("test3"),
            Text("test4"),
        ]
    )

    assert message.only("text") is False

    message = MessageFactory(
        [
            Text("test"),
            Text("test"),
        ]
    )

    assert message.only(Text("test")) is True


def test_message_join():
    msg = MessageFactory([Text("test")])
    iterable = [
        Text("first"),
        MessageFactory([Text("second"), Text("third")]),
    ]

    assert msg.join(iterable) == MessageFactory(
        [
            Text("first"),
            Text("test"),
            Text("second"),
            Text("third"),
        ]
    )


def test_message_include():
    message = MessageFactory(
        [
            Text("test"),
            Image("test2"),
            Image("test3"),
            Text("test4"),
        ]
    )

    assert message.include("text") == MessageFactory(
        [
            Text("test"),
            Text("test4"),
        ]
    )


def test_message_exclude():
    message = MessageFactory(
        [
            Text("test"),
            Image("test2"),
            Image("test3"),
            Text("test4"),
        ]
    )

    assert message.exclude("image") == MessageFactory(
        [
            Text("test"),
            Text("test4"),
        ]
    )
