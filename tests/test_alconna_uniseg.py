from typing import Type
from typing_extensions import override

from nonebug import App

from .utils import ob12_kwargs, mock_obv12_message_event


async def test_alc_builder(app: App):
    from nonebot import get_driver, get_adapter
    from nonebot_plugin_alconna import Other, Custom
    from nonebot.adapters.onebot.v12 import Bot, Adapter, Message, MessageSegment

    from nonebot_plugin_saa.ext.uniseg import (
        Fallback,
        AlcSegmentBuildError,
        alc_builder,
    )

    driver = get_driver()
    driver.register_adapter(Adapter)

    class OkCustom(Custom):
        @override
        def export(self, msg_type: Type[Message]) -> MessageSegment:
            return MessageSegment.text("ok")

    class ErrCustom(Custom):
        @override
        def export(self, msg_type: Type[Message]) -> MessageSegment:
            raise AlcSegmentBuildError("err")

    o = Other(MessageSegment.text("other"))

    bot = Bot(
        get_adapter(Adapter.get_name()), self_id="test", **ob12_kwargs()  # type: ignore
    )

    assert await alc_builder(
        {
            "uniseg": OkCustom(mstype="text", content="?"),
            "fallback": Fallback.Forbid,
        },
        bot,
    ) == MessageSegment.text("ok")

    assert await alc_builder(
        {"uniseg": o, "fallback": Fallback.Permit}, bot
    ) == MessageSegment.text("other")

    assert await alc_builder(
        {
            "uniseg": ErrCustom(mstype="text", content="?"),
            "fallback": Fallback.Permit,
        },
        bot,
    ) == MessageSegment.text(str(ErrCustom(mstype="text", content="?")))


async def test_build(app: App):
    from nonebot_plugin_alconna import File as AF
    from nonebot_plugin_alconna import Text as AT
    from nonebot_plugin_alconna import UniMessage
    from nonebot_plugin_alconna import Image as AI

    from nonebot_plugin_saa import Text as ST
    from nonebot_plugin_saa import Image as SI
    from nonebot_plugin_saa.ext.uniseg import (
        UniMessageFactory,
        AlcMessageSegmentFactory,
    )

    # single
    assert UniMessageFactory() is not None
    assert UniMessageFactory("#s0 str")
    assert UniMessageFactory(AT("#s1 alc t1"))
    assert UniMessageFactory(ST("#s2 saa t1"))
    assert UniMessageFactory(AI(url="https://a.lc/i1#s3"))
    assert UniMessageFactory(SI(b"#s4 saa t1"))
    assert UniMessageFactory(AF(url="https://a.lc/f1#s5"))
    # multi
    assert UniMessageFactory([AT("#m1 alc t1"), AT("#m1 alc t2")])
    assert UniMessageFactory([ST("#m2 saa t1"), ST("#m2 saa t2")])
    assert UniMessageFactory([AI(url="https://a.lc/i1#m3"), SI("https://a.lc/i2#m3")])
    assert UniMessageFactory([AF(url="https://a.lc/f1#m4"), ST("#m4 saa t1")])
    assert UniMessageFactory(
        ["#m5 str1", "#m5 str2", AF(url="https://a.lc/f1#m5"), SI("https://a.lc/i1#m5")]
    )
    # from
    m1 = UniMessageFactory.from_unimsg(
        UniMessage([AT("#f1 alc t1"), AI("#f1 alc i1"), AF("#f1 alc f1")])
    )
    assert len(m1) == 3

    assert AlcMessageSegmentFactory(AT("#f1 alc t1"))
    assert AlcMessageSegmentFactory.from_str("#f1 alc t1") == AlcMessageSegmentFactory(
        AT("#f1 alc t1")
    )
    assert AlcMessageSegmentFactory.from_unimsg(
        UniMessage([AT("#f1 alc t1"), AI("#f1 alc i1"), AF("#f1 alc f1")])
    ) == [
        AlcMessageSegmentFactory(AT("#f1 alc t1")),
        AlcMessageSegmentFactory(AI("#f1 alc i1")),
        AlcMessageSegmentFactory(AF("#f1 alc f1")),
    ]


async def test_send(app: App):
    from nonebot import get_driver, on_message
    from nonebot_plugin_alconna import File as AF
    from nonebot_plugin_alconna import Text as AT
    from nonebot_plugin_alconna import Image as AI
    from nonebot.adapters.onebot.v12 import (
        Bot,
        Message,
        MessageSegment,
        PrivateMessageEvent,
    )

    from nonebot_plugin_saa import Text as ST
    from nonebot_plugin_saa import Image as SI
    from nonebot_plugin_saa import SupportedAdapters
    from nonebot_plugin_saa.ext.uniseg import UniMessageFactory

    matcher = on_message()

    @matcher.handle()
    async def process(msg: PrivateMessageEvent):
        await UniMessageFactory([AT("#1 alc t1"), AT("#1 alc t2")]).send()
        await UniMessageFactory([ST("#2 saa t1"), ST("#2 saa t2")]).send()
        await UniMessageFactory([AT("#3 alc t1"), ST("#3 saa t1")]).send()
        await UniMessageFactory([AT("#4 alc t1"), SI("#4 saa i1")]).send()
        await UniMessageFactory([AI(url="https://a.lc/i1#5"), ST("#5 saa t1")]).send()
        await UniMessageFactory([AI(url="https://a/lc/i1#6"), SI(b"#6 saa t1")]).send()
        await UniMessageFactory([AF(url="https://a.lc/f1#7"), ST("#7 saa t1")]).send()

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.onebot_v12)]
        bot = ctx.create_bot(
            base=Bot, adapter=adapter_obj, **ob12_kwargs(platform="qq")
        )
        msg_event = mock_obv12_message_event(Message("321"))
        ctx.receive_event(bot, msg_event)
        # 1
        ctx.should_call_api(
            "send_message",
            data={
                "message": Message(
                    [MessageSegment.text("#1 alc t1"), MessageSegment.text("#1 alc t2")]
                ),
                "user_id": "2233",
                "detail_type": "private",
            },
            result={"message_id": "1"},
        )
        # 2
        ctx.should_call_api(
            "send_message",
            data={
                "message": Message(
                    [MessageSegment.text("#2 saa t1"), MessageSegment.text("#2 saa t2")]
                ),
                "user_id": "2233",
                "detail_type": "private",
            },
            result={"message_id": "2"},
        )
        # 3
        ctx.should_call_api(
            "send_message",
            data={
                "message": Message(
                    [MessageSegment.text("#3 alc t1"), MessageSegment.text("#3 saa t1")]
                ),
                "user_id": "2233",
                "detail_type": "private",
            },
            result={"message_id": "3"},
        )
        # 4
        ctx.should_call_api(
            "upload_file",
            {"type": "url", "name": "image", "url": "#4 saa i1"},
            {"file_id": "#4 saa i1 id"},
        )
        ctx.should_call_api(
            "send_message",
            data={
                "message": Message(
                    [
                        MessageSegment.text("#4 alc t1"),
                        MessageSegment.image("#4 saa i1 id"),
                    ]
                ),
                "user_id": "2233",
                "detail_type": "private",
            },
            result={"message_id": "4"},
        )
        # 5
        ctx.should_call_api(
            "upload_file",
            {"type": "url", "name": "image.png", "url": "https://a.lc/i1#5"},
            {"file_id": "#5 alc i1 id"},
        )
        ctx.should_call_api(
            "send_message",
            data={
                "message": Message(
                    [
                        MessageSegment.image("#5 alc i1 id"),
                        MessageSegment.text("#5 saa t1"),
                    ]
                ),
                "user_id": "2233",
                "detail_type": "private",
            },
            result={"message_id": "5"},
        )
        # 6
        ctx.should_call_api(
            "upload_file",
            {"type": "url", "name": "image.png", "url": "https://a/lc/i1#6"},
            {"file_id": "#6 alc i1 id"},
        )
        ctx.should_call_api(
            "upload_file",
            {"type": "data", "name": "image", "data": b"#6 saa t1"},
            {"file_id": "#6 saa i1 id"},
        )
        ctx.should_call_api(
            "send_message",
            data={
                "message": Message(
                    [
                        MessageSegment.image("#6 alc i1 id"),
                        MessageSegment.image(file_id="#6 saa i1 id"),
                    ]
                ),
                "user_id": "2233",
                "detail_type": "private",
            },
            result={"message_id": "6"},
        )
        # # 7
        ctx.should_call_api(
            "upload_file",
            {"type": "url", "name": "file.bin", "url": "https://a.lc/f1#7"},
            {"file_id": "#7 alc f1 id"},
        )
        ctx.should_call_api(
            "send_message",
            data={
                "message": Message(
                    [
                        MessageSegment.file("#7 alc f1 id"),
                        MessageSegment.text("#7 saa t1"),
                    ]
                ),
                "user_id": "2233",
                "detail_type": "private",
            },
            result={"message_id": "7"},
        )
