from io import BytesIO
from pathlib import Path
from datetime import datetime
from functools import partial

import httpx
import respx
import pytest
from nonebug import App
from nonebot import get_driver
from nonebot.adapters.discord import Bot
from nonebot.adapters.discord.config import BotInfo

from .utils import assert_ms, mock_discord_message_event

discord_bot_info = BotInfo(token="123")
discord_kwargs = {"self_id": "2333", "bot_info": discord_bot_info}


@pytest.fixture
def assert_discord(app: App):
    from nonebot_plugin_saa import SupportedAdapters

    return partial(
        assert_ms,
        Bot,
        SupportedAdapters.discord,
        bot_info=discord_bot_info,
        self_id=discord_kwargs["self_id"],
    )


async def test_text(app: App, assert_discord):
    from nonebot.adapters.discord import MessageSegment

    from nonebot_plugin_saa import Text

    await assert_discord(app, Text("123"), MessageSegment.text("123"))


@respx.mock
async def test_image(app: App, assert_discord, tmp_path: Path):
    from nonebot.adapters.discord import MessageSegment

    from nonebot_plugin_saa import Image

    image_route = respx.get("https://example.com/amiya.png")
    image_route.mock(return_value=httpx.Response(200, content=b"amiya"))

    data = b"\x89PNG\r"
    await assert_discord(
        app,
        Image(data),
        MessageSegment.attachment(file="image", content=b"\x89PNG\r"),
    )

    data = BytesIO(b"\x89PNG\r")
    await assert_discord(
        app,
        Image(data.read()),
        MessageSegment.attachment(file="image", content=b"\x89PNG\r"),
    )

    temp_image_path = tmp_path / "amiya.png"
    with temp_image_path.open("wb") as f:
        f.write(b"\x89PNG\r")

    await assert_discord(
        app,
        Image(temp_image_path),
        MessageSegment.attachment(file=temp_image_path.name, content=b"\x89PNG\r"),
    )

    await assert_discord(
        app,
        Image("https://example.com/amiya.png"),
        MessageSegment.attachment(file="image", content=b"amiya"),
    )

    with pytest.raises(TypeError):
        await assert_discord(
            app,
            Image(1),  # type: ignore
            MessageSegment.attachment(file="1.png", content=b"\x89PNG\r"),
        )


async def test_mention(app: App, assert_discord):
    from nonebot.adapters.discord import MessageSegment

    from nonebot_plugin_saa import Mention

    await assert_discord(app, Mention("123"), MessageSegment.mention_user(int("123")))


async def test_mention_all(app: App, assert_discord):
    from nonebot.adapters.discord import MessageSegment

    from nonebot_plugin_saa import MentionAll

    await assert_discord(app, MentionAll(), MessageSegment.mention_everyone())


async def test_reply(app: App, assert_discord):
    from nonebot.adapters.discord import MessageSegment

    from nonebot_plugin_saa import Reply
    from nonebot_plugin_saa.adapters.discord import DiscordMessageId

    await assert_discord(
        app, Reply(DiscordMessageId(message_id=123)), MessageSegment.reference(123)
    )


async def test_send(app: App):
    from nonebot import on_message
    from nonebot.adapters.discord import Bot
    from nonebot.adapters.discord.api.model import (
        User,
        Snowflake,
        MessageGet,
        MessageType,
    )

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters

    matcher = on_message()

    @matcher.handle()
    async def process():
        await MessageFactory(Text("123")).send()

    data = {
        "channel_id": 4321,
        "nonce": None,
        "tts": False,
        "allowed_mentions": None,
        "content": "123",
    }
    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.discord)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **discord_kwargs)
        msg_event = mock_discord_message_event()
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "create_message",
            data=data,
            result=MessageGet(
                id=Snowflake(1234),
                channel_id=Snowflake(4321),
                author=User(
                    id=Snowflake(1234),
                    username="canxin121",
                    discriminator="0",
                    avatar=None,
                    global_name=None,
                ),
                content="/test",
                timestamp=datetime(year=1999, month=9, day=9),
                edited_timestamp=None,
                tts=False,
                mention_everyone=False,
                mentions=[],
                mention_roles=[],
                attachments=[],
                embeds=[],
                pinned=False,
                type=MessageType(0),
            ),
        )

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.discord)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **discord_kwargs)
        msg_event = mock_discord_message_event(False)
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "create_message",
            data=data,
            result=MessageGet(
                id=Snowflake(1234),
                channel_id=Snowflake(4321),
                author=User(
                    id=Snowflake(1234),
                    username="canxin121",
                    discriminator="0",
                    avatar=None,
                    global_name=None,
                ),
                content="/test",
                timestamp=datetime(year=1999, month=9, day=9),
                edited_timestamp=None,
                tts=False,
                mention_everyone=False,
                mentions=[],
                mention_roles=[],
                attachments=[],
                embeds=[],
                pinned=False,
                type=MessageType(0),
            ),
        )
