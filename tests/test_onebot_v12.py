from pathlib import Path
from functools import partial

from nonebug import App
from nonebot.adapters.onebot.v12 import Bot, MessageSegment

from nonebot_plugin_send_anything_anywhere import Text, Image
from nonebot_plugin_send_anything_anywhere.utils import SupportedAdapters

from .utils import assert_ms, make_fake_bot

assert_onebot_v12 = partial(assert_ms, Bot, SupportedAdapters.onebot_v12, platform="qq")


async def test_text(app: App):
    await assert_onebot_v12(app, Text("123"), MessageSegment.text("123"))


async def test_image(app: App):
    async with app.test_api() as ctx:
        bot = make_fake_bot(
            ctx, str(SupportedAdapters.onebot_v12), Bot, "314159", platform="qq"
        )
        ctx.should_call_api(
            "upload_file",
            {"type": "url", "name": "image", "url": "https://example.com/image.png"},
            {"file_id": "123"},
        )
        generated_ms = await Image("https://example.com/image.png").build(bot)
        assert generated_ms == MessageSegment.image("123")

    async with app.test_api() as ctx:
        bot = make_fake_bot(
            ctx, str(SupportedAdapters.onebot_v12), Bot, "314159", platform="qq"
        )

        data = b"\x89PNG\r"

        ctx.should_call_api(
            "upload_file",
            {"type": "data", "name": "image", "data": data},
            {"file_id": "123"},
        )
        generated_ms = await Image(data).build(bot)
        assert generated_ms == MessageSegment.image("123")

    async with app.test_api() as ctx:
        bot = make_fake_bot(
            ctx, str(SupportedAdapters.onebot_v12), Bot, "314159", platform="qq"
        )

        image_path = Path(__file__).parent / "image.png"

        ctx.should_call_api(
            "upload_file",
            {"type": "path", "name": "image", "path": str(image_path.resolve())},
            {"file_id": "123"},
        )
        generated_ms = await Image(image_path).build(bot)
        assert generated_ms == MessageSegment.image("123")
