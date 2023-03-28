from functools import partial
from io import BytesIO

from nonebot import get_driver
from nonebot.adapters.kaiheila import Bot
from nonebot.adapters.kaiheila.api import URL
from nonebug import App

from nonebot_plugin_saa.utils import SupportedAdapters
from .utils import assert_ms, mock_kaiheila_message_event, kaiheila_kwargs

assert_kaiheila = partial(assert_ms, Bot, SupportedAdapters.kaiheila, **kaiheila_kwargs())


async def test_text(app: App):
    from nonebot.adapters.kaiheila import MessageSegment

    from nonebot_plugin_saa import Text

    await assert_kaiheila(app, Text("123"), MessageSegment.text("123"))


async def test_image(app: App):
    from nonebot.adapters.kaiheila import MessageSegment

    from nonebot_plugin_saa import Image

    adapter = get_driver()._adapters[str(SupportedAdapters.kaiheila)]
    async with app.test_api() as ctx:
        bot = ctx.create_bot(
            base=Bot, adapter=adapter, self_id="2233", **kaiheila_kwargs()
        )

        data = BytesIO(b"\x89PNG\r")

        ctx.should_call_api(
            "asset_create",
            {'file': ('image', b'\x89PNG\r', 'application/octet-stream')},
            URL(url="123"),
        )
        generated_ms = await Image(data).build(bot)
        assert generated_ms == MessageSegment.image("123")


async def test_mention(app: App):
    from nonebot.adapters.kaiheila import MessageSegment

    from nonebot_plugin_saa import Mention

    await assert_kaiheila(app, Mention("123"), MessageSegment.KMarkdown("(met)123(met)"))


async def test_reply(app: App):
    from nonebot.adapters.kaiheila import MessageSegment

    from nonebot_plugin_saa import Reply

    await assert_kaiheila(app, Reply("123"), MessageSegment.quote("123"))


async def test_send(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.kaiheila import Bot

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters

    matcher = on_message()

    @matcher.handle()
    async def process():
        await MessageFactory(Text("123")).send()

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.kaiheila)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **kaiheila_kwargs())
        msg_event = mock_kaiheila_message_event()
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "direct-message/create",
            data={'type': 1, 'content': '123', 'target_id': '3344'},
            result=None,
        )

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.kaiheila)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **kaiheila_kwargs())
        msg_event = mock_kaiheila_message_event(channel=True)
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "message/create",
            data={'type': 1, 'content': '123', 'target_id': '1111'},
            result=None,
        )


async def test_send_with_reply(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.kaiheila import Bot

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters

    matcher = on_message()

    @matcher.handle()
    async def process():
        await MessageFactory(Text("123")).send(reply=True, at_sender=True)

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.kaiheila)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **kaiheila_kwargs())
        msg_event = mock_kaiheila_message_event()
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "direct-message/create",
            data={'type': 9, 'content': '(met)3344(met)123', 'quote': 'abcdef', 'target_id': '3344'},
            result=None,
        )

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.kaiheila)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **kaiheila_kwargs())
        msg_event = mock_kaiheila_message_event(channel=True)
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "message/create",
            data={'type': 9, 'content': '(met)3344(met)123', 'quote': 'abcdef', 'target_id': '1111'},
            result=None,
        )


async def test_send_active(app: App):
    from nonebot import get_driver

    from nonebot_plugin_saa import MessageFactory
    from nonebot_plugin_saa.utils.platform_send_target import TargetKaiheilaPrivate, TargetKaiheilaChannel

    async with app.test_api() as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.kaiheila)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **kaiheila_kwargs())

        send_target_private = TargetKaiheilaPrivate(user_id="3344")
        ctx.should_call_api(
            "direct-message/create",
            data={'type': 1, 'content': '123', 'target_id': '3344'},
            result=None,
        )
        await MessageFactory("123").send_to(bot, send_target_private)

        send_target_group = TargetKaiheilaChannel(channel_id="1111")
        ctx.should_call_api(
            "message/create",
            data={'type': 1, 'content': '123', 'target_id': '1111'},
            result=None,
        )
        await MessageFactory("123").send_to(bot, send_target_group)
