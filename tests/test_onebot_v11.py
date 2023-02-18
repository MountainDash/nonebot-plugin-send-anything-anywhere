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


async def test_image(app: App):
    from nonebot.adapters.onebot.v11 import MessageSegment

    from nonebot_plugin_send_anything_anywhere import Image

    await assert_onebot_v11(app, Image("123"), MessageSegment.image("123"))


async def test_mention(app: App):
    from nonebot.adapters.onebot.v11 import MessageSegment

    from nonebot_plugin_send_anything_anywhere import Mention

    await assert_onebot_v11(app, Mention("123"), MessageSegment.at("123"))


async def test_reply(app: App):
    from nonebot.adapters.onebot.v11 import MessageSegment

    from nonebot_plugin_send_anything_anywhere import Reply

    await assert_onebot_v11(app, Reply(123), MessageSegment.reply(123))
