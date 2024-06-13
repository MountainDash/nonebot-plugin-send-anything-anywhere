from io import BytesIO
from pathlib import Path
from functools import partial

import pytest
from nonebug import App
from grpclib.client import Channel
from nonebot.adapters.kritor import Bot
from nonebot.adapters.kritor.config import ClientInfo

from .utils import assert_ms

kritor_bot_config = ClientInfo(
    host="localhost",
    port=8080,
    account="1919810",
    ticket="233333",
)
kritor_kwargs = {
    "self_id": "1919810",
    "info": kritor_bot_config,
    "client": Channel("localhost", 8080),
}


@pytest.fixture
def assert_kritor(app: App):
    from nonebot_plugin_saa import SupportedAdapters

    return partial(
        assert_ms,
        Bot,
        SupportedAdapters.kritor,
        **kritor_kwargs,
    )


async def test_text(app: App, assert_kritor):
    from nonebot.adapters.kritor import MessageSegment

    from nonebot_plugin_saa import Text

    await assert_kritor(
        app, Text("Hello, World!"), MessageSegment.text("Hello, World!")
    )


async def test_image(app: App, assert_kritor, tmp_path: Path):
    from nonebot.adapters.kritor import MessageSegment

    from nonebot_plugin_saa import Image

    tmp_image = tmp_path / "image.jpg"
    tmp_image.write_bytes(b"Hello, World!")

    await assert_kritor(
        app,
        Image("https://example.com/image.jpg"),
        MessageSegment.image(url="https://example.com/image.jpg"),
    )
    await assert_kritor(
        app,
        Image("http://example.com/image.jpg"),
        MessageSegment.image(url="http://example.com/image.jpg"),
    )
    await assert_kritor(
        app,
        Image(tmp_image.as_posix()),
        MessageSegment.image(path=tmp_image.as_posix()),
    )
    await assert_kritor(app, Image(tmp_image), MessageSegment.image(path=tmp_image))
    await assert_kritor(
        app, Image(b"Hello, World!"), MessageSegment.image(raw=b"Hello, World!")
    )
    await assert_kritor(
        app,
        Image(BytesIO(b"Hello, World!")),
        MessageSegment.image(raw=BytesIO(b"Hello, World!")),
    )
    with pytest.raises(TypeError, match="Invalid image str"):
        await assert_kritor(app, Image("Hello, World!"), None)

    with pytest.raises(TypeError, match="Unsupported type of"):
        await assert_kritor(app, Image(123), None)  # type: ignore


async def test_mention(app: App, assert_kritor):
    from nonebot.adapters.kritor import MessageSegment

    from nonebot_plugin_saa import Mention

    await assert_kritor(
        app,
        Mention("123"),
        MessageSegment.at(uid="123"),
    )


async def test_mention_all(app: App, assert_kritor):
    from nonebot.adapters.kritor import MessageSegment

    from nonebot_plugin_saa import MentionAll

    await assert_kritor(
        app,
        MentionAll(),
        MessageSegment.atall(),
    )


async def test_reply(app: App, assert_kritor):
    from nonebot.adapters.kritor import MessageSegment

    from nonebot_plugin_saa import Reply
    from nonebot_plugin_saa.adapters.kritor import KritorMessageId

    await assert_kritor(
        app,
        Reply(KritorMessageId(message_id="123")),
        MessageSegment.reply(message_id="123"),
    )
