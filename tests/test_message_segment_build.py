from typing import TYPE_CHECKING, Type

import pytest
from nonebug import App

from .utils import assert_ms

if TYPE_CHECKING:
    from nonebot_plugin_saa.utils import SupportedAdapters, MessageSegmentFactory

    class MyText(MessageSegmentFactory):
        text: str

        def __init__(self, text: str) -> None:
            self.text = text
            super().__init__()


@pytest.fixture
def dummy_factory(app: App):
    from nonebot_plugin_saa.utils import MessageSegmentFactory

    class MyText(MessageSegmentFactory):
        text: str

        def __init__(self, text: str) -> None:
            self.text = text
            super().__init__()

    class _Test(MyText):
        pass

    return _Test


@pytest.fixture
def onebot_v11(app: App):
    from nonebot_plugin_saa.utils import SupportedAdapters

    return SupportedAdapters.onebot_v11


async def test_sync_without_bot(
    app: App, dummy_factory: "Type[MyText]", onebot_v11: "SupportedAdapters"
):
    from nonebot.adapters.onebot.v11.bot import Bot
    from nonebot.adapters.onebot.v11.message import MessageSegment

    from nonebot_plugin_saa.utils import SupportedAdapters, register_ms_adapter

    @register_ms_adapter(onebot_v11, dummy_factory)
    def _text(t):
        return MessageSegment.text("314159")

    await assert_ms(
        Bot,
        SupportedAdapters.onebot_v11,
        app,
        dummy_factory("314159"),
        MessageSegment.text("314159"),
    )


async def test_sync_with_bot(
    app: App, dummy_factory: "Type[MyText]", onebot_v11: "SupportedAdapters"
):
    from nonebot.adapters.onebot.v11.bot import Bot
    from nonebot.adapters.onebot.v11.message import MessageSegment

    from nonebot_plugin_saa.utils import SupportedAdapters, register_ms_adapter

    @register_ms_adapter(onebot_v11, dummy_factory)
    def _text(t, bot):
        return MessageSegment.text("314159")

    await assert_ms(
        Bot,
        SupportedAdapters.onebot_v11,
        app,
        dummy_factory("314159"),
        MessageSegment.text("314159"),
    )


async def test_async_without_bot(
    app: App, dummy_factory: "Type[MyText]", onebot_v11: "SupportedAdapters"
):
    from nonebot.adapters.onebot.v11.bot import Bot
    from nonebot.adapters.onebot.v11.message import MessageSegment

    from nonebot_plugin_saa.utils import SupportedAdapters, register_ms_adapter

    @register_ms_adapter(onebot_v11, dummy_factory)
    async def _text(t):
        return MessageSegment.text("314159")

    await assert_ms(
        Bot,
        SupportedAdapters.onebot_v11,
        app,
        dummy_factory("314159"),
        MessageSegment.text("314159"),
    )


async def test_async_with_bot(
    app: App, dummy_factory: "Type[MyText]", onebot_v11: "SupportedAdapters"
):
    from nonebot.adapters.onebot.v11.bot import Bot
    from nonebot.adapters.onebot.v11.message import MessageSegment

    from nonebot_plugin_saa.utils import SupportedAdapters, register_ms_adapter

    @register_ms_adapter(onebot_v11, dummy_factory)
    async def _text(t, bot):
        return MessageSegment.text("314159")

    await assert_ms(
        Bot,
        SupportedAdapters.onebot_v11,
        app,
        dummy_factory("314159"),
        MessageSegment.text("314159"),
    )
