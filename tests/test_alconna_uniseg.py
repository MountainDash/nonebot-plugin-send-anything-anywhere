from nonebug import App

from .utils import ob12_kwargs, mock_obv12_message_event


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
