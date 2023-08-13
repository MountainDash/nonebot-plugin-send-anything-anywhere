# ruff: noqa: E402
import tempfile
import threading
from io import BytesIO
from pathlib import Path

import pytest
import uvicorn
from fastapi import FastAPI
from fastapi.responses import FileResponse

pytest.importorskip("nonebot.adapters.discord")

from functools import partial

import nonebot
from nonebot.params import Event
from nonebug import App
from nonebot import get_driver
from nonebot.adapters.discord import Bot, Adapter
from nonebot.adapters.discord.message import TextSegment
from nonebot.adapters.discord.api import (
    User,
    MessageType,
    MessageFlag,
)
from nonebot.adapters.discord.config import BotInfo
from nonebot.adapters.discord.event import EventType
from nonebot_plugin_saa.utils import SupportedAdapters

from .utils import assert_ms


@pytest.fixture(scope="session", autouse=True)
def load_adapters(nonebug_init: None):
    driver = nonebot.get_driver()
    driver.register_adapter(Adapter)


def discord_kwargs():
    return {"self_id": "2333", "bot_info": BotInfo(token=123)}


def mock_discord_message_event(create: bool = True):
    from nonebot.adapters.discord.event import (
        MessageEvent as DiscordMessageEvent,
    )
    from nonebot.adapters.discord.event import (
        MessageCreateEvent as DiscordMessageCreateEvent,
    )
    event_args = {
        'id': 1234,
        'channel_id': 4321,
        'author': User(**{'id': 1234,
                          'username': '.canxin121',
                          'discriminator': '0',
                          'avatar': None}),
        'content': '/test',
        'timestamp': 1,
        'edited_timestamp': None,
        'tts': False, 'mention_everyone': False,
        'mentions': [], 'mention_roles': [],
        'attachments': [], 'embeds': [], 'nonce': 3210,
        'pinned': False, 'type': MessageType(0),
        'flags'
        : MessageFlag(0),
        'referenced_message': None,
        'components': [],
        'to_me': False,
        'reply': None,
        '_message': [
            TextSegment(type='text',
                        data={'text': '/test'
                              }
                        )
        ]
    }

    if not create:
        return DiscordMessageEvent(__type__=EventType.MESSAGE_CREATE, **event_args)
    else:
        return DiscordMessageCreateEvent(**event_args)


assert_discord = partial(
    assert_ms, Bot, SupportedAdapters.discord, **discord_kwargs()
)


async def test_text(app: App):
    from nonebot.adapters.discord import MessageSegment

    from nonebot_plugin_saa import Text

    await assert_discord(app, Text("123"), MessageSegment.text("123"))


async def test_image(app: App):
    from nonebot.adapters.discord import MessageSegment

    from nonebot_plugin_saa import Image
    data = BytesIO(b"\x89PNG\r")
    await assert_discord(app, Image(data), MessageSegment.attachment(file="image.png", content=b"\x89PNG\r"))
    data = BytesIO(b"\x89PNG\r")
    await assert_discord(app, Image(data.read()), MessageSegment.attachment(file="image.png", content=b"\x89PNG\r"))

    with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
        temp_file_path = Path(temp_file.name)
        with open(temp_file_path, "wb") as f:
            f.write(b"\x89PNG\r")
        await assert_discord(app, Image(temp_file_path),
                             MessageSegment.attachment(file=temp_file_path.name, content=b"\x89PNG\r"))
        await assert_discord(app, Image(str(temp_file_path)),
                             MessageSegment.attachment(file=temp_file_path.name, content=b"\x89PNG\r"))
        faapp = FastAPI()

        @faapp.get("/image.png")
        async def get_image():
            return FileResponse(path=temp_file_path, media_type='image/png')

        async def run_server():
            web_ui_thread = threading.Thread(
                target=lambda: uvicorn.run(faapp, host="127.0.0.1", port=2312))
            web_ui_thread.daemon = True
            web_ui_thread.start()

        await run_server()
        await assert_discord(app, Image(str("http://127.0.0.1:2312/image.png")),
                             MessageSegment.attachment(file="image.png", content=b"\x89PNG\r"))
    try:
        await assert_discord(app, Image(1), MessageSegment.attachment(file="1.png", content=b"\x89PNG\r"))
    except:
        pass


async def test_mention(app: App):
    from nonebot.adapters.discord import MessageSegment

    from nonebot_plugin_saa import Mention

    await assert_discord(
        app, Mention("123"), MessageSegment.mention_user(int("123"))
    )


async def test_reply(app: App):
    from nonebot.adapters.discord import MessageSegment

    from nonebot_plugin_saa import Reply

    await assert_discord(app, Reply("123"), MessageSegment.reference(int("123")))


async def test_send(app: App):
    from nonebot.adapters.discord import Bot
    from nonebot import on_message

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters

    matcher = on_message()

    @matcher.handle()
    async def process():
        await MessageFactory(Text("123")).send()

    data = {"data": {
        "channel_id": 4321,
        "nonce": None,
        "tts": False,
        "allowed_mentions": None,
        'attachments': None,
        'components': None,
        'content': '123',
        'embeds': None,
        'files': None,
        'message_reference': None,
        'sticker_ids': None
    }}
    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.discord)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **discord_kwargs())
        msg_event = mock_discord_message_event()
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "create_message",
            **data
        )

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.discord)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **discord_kwargs())
        msg_event = mock_discord_message_event(False)
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "create_message",
            **data
        )


async def test_send_to(app: App):
    from nonebot.adapters.discord import Bot
    from nonebot import on_message

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters, TargetDiscordChannel

    matcher = on_message()

    @matcher.handle()
    async def process(event: Event, bot: Bot):
        await MessageFactory(Text("123")).send_to(TargetDiscordChannel(channel_id=event.channel_id),bot=bot)

    data = {"data": {
        "channel_id": 4321,
        "nonce": None,
        "tts": False,
        "allowed_mentions": None,
        'attachments': None,
        'components': None,
        'content': '123',
        'embeds': None,
        'files': None,
        'message_reference': None,
        'sticker_ids': None
    }}
    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.discord)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **discord_kwargs())
        msg_event = mock_discord_message_event()
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "create_message",
            **data
        )

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.discord)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **discord_kwargs())
        msg_event = mock_discord_message_event(False)
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "create_message",
            **data
        )
