from functools import partial

from nonebug import App
from nonebot.adapters.onebot.v11.bot import Bot

from nonebot_plugin_send_anything_anywhere.utils import SupportedAdapters

from .utils import assert_ms

assert_onebot_v11 = partial(assert_ms, Bot, SupportedAdapters.onebot_v11)


async def test_text(app: App):
    from nonebot.adapters.onebot.v11 import MessageSegment

    from nonebot_plugin_send_anything_anywhere import Text

    await assert_onebot_v11(app, Text("123"), MessageSegment.text("123"))
