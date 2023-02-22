from typing import TYPE_CHECKING, Type

from nonebot import get_driver

if TYPE_CHECKING:
    from nonebug import App
    from nonebot.internal.adapter.bot import Bot
    from nonebot.internal.adapter.message import MessageSegment

    from nonebot_plugin_saa.utils import SupportedAdapters, MessageSegmentFactory


async def assert_ms(
    bot_base: "Type[Bot]",
    adapter: "SupportedAdapters",
    app: "App",
    ms_factory: "MessageSegmentFactory",
    ms: "MessageSegment",
    **kwargs,
):
    if not kwargs:
        kwargs["self_id"] = "314159"

    async with app.test_api() as ctx:
        adapter_obj = get_driver()._adapters[str(adapter)]
        bot = ctx.create_bot(base=bot_base, adapter=adapter_obj, **kwargs)
        generated_ms = await ms_factory.build(bot)
        assert generated_ms.data == ms.data
