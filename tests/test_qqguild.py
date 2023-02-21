from pathlib import Path
from functools import partial

from nonebug import App
from nonebot.adapters.qqguild import Bot
from nonebot.adapters.qqguild.config import BotInfo

from nonebot_plugin_saa.utils import SupportedAdapters

from .utils import assert_ms

assert_qqguild = partial(
    assert_ms,
    Bot,
    SupportedAdapters.qqguild,
    bot_info=BotInfo(id="314159", token="token", secret="secret"),
)


async def test_text(app: App):
    from nonebot.adapters.qqguild import MessageSegment

    from nonebot_plugin_saa import Text

    await assert_qqguild(app, Text("text"), MessageSegment.text("text"))


async def test_image(app: App, tmp_path: Path):
    from nonebot.adapters.qqguild import MessageSegment

    from nonebot_plugin_saa import Image

    await assert_qqguild(
        app,
        Image("https://picsum.photos/200"),
        MessageSegment.image("https://picsum.photos/200"),
    )

    data = b"\x89PNG\r"
    await assert_qqguild(app, Image(data), MessageSegment.file_image(data))

    image_path = tmp_path / "image.png"
    with open(image_path, "wb") as f:
        f.write(data)
    await assert_qqguild(app, Image(image_path), MessageSegment.file_image(image_path))


async def test_mention_user(app: App):
    from nonebot.adapters.qqguild import MessageSegment

    from nonebot_plugin_saa import Mention

    await assert_qqguild(app, Mention("314159"), MessageSegment.mention_user(314159))
