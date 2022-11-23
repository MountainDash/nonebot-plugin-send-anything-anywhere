from typing import TYPE_CHECKING, Any, Type, Union, Optional

if TYPE_CHECKING:
    from nonebug import App
    from nonebot.internal.adapter.bot import Bot
    from nonebug.mixin.call_api import ApiContext
    from nonebot.internal.adapter.message import MessageSegment

    from nonebot_plugin_send_anything_anywhere.utils import (
        SupportedAdapters,
        MessageSegmentFactory,
    )


def make_fake_bot(
    ctx: "ApiContext", adapter_name: str, bot: Optional[Type["Bot"]], self_id: str
) -> "Bot":
    from nonebot import get_driver
    from nonebot.drivers import Driver
    from nonebot.typing import overrides
    from nonebot.internal.adapter.bot import Bot
    from nonebot.internal.adapter.event import Event
    from nonebot.internal.adapter.adapter import Adapter
    from nonebot.internal.adapter.message import Message, MessageSegment

    class FakeAdapter(Adapter):
        @overrides(Adapter)
        def __init__(self, driver: Driver, ctx: "ApiContext", **kwargs: Any):
            super(FakeAdapter, self).__init__(driver, **kwargs)
            self.ctx = ctx

        @classmethod
        @overrides(Adapter)
        def get_name(cls) -> str:
            return adapter_name

        @overrides(Adapter)
        async def _call_api(self, bot: Bot, api: str, **data) -> Any:
            return self.ctx.got_call_api(api, **data)

    base = bot or Bot

    class FakeBot(base):
        @property
        def ctx(self) -> "ApiContext":
            return self.adapter.ctx  # type: ignore

        @overrides(base)
        async def send(
            self,
            event: "Event",
            message: Union[str, "Message", "MessageSegment"],
            **kwargs,
        ) -> Any:
            return self.ctx.got_call_send(event, message, **kwargs)

    return FakeBot(FakeAdapter(get_driver(), ctx), self_id)


async def assert_ms(
    bot_base: "Type[Bot]",
    adapter: "SupportedAdapters",
    app: "App",
    ms_factory: "MessageSegmentFactory",
    ms: "MessageSegment",
):
    async with app.test_api() as ctx:
        bot = make_fake_bot(ctx, str(adapter), bot_base, "314159")
        generated_ms = await ms_factory.convert(bot)
        assert generated_ms.data == ms.data
