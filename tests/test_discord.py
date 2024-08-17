from io import BytesIO
from pathlib import Path
from copy import deepcopy
from datetime import datetime
from functools import partial

import httpx
import respx
import pytest

pytest.importorskip("nonebot.adapters.discord")
from nonebug import App
from nonebot import get_driver
from pytest_mock import MockerFixture
from nonebot.adapters.discord import Bot, Adapter
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
        Image(data),
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

    temp_image_path = tmp_path / "nonebot.ddl"
    with temp_image_path.open("wb") as f:
        f.write(b"ddl")

    await assert_discord(
        app,
        Image(temp_image_path),
        MessageSegment.attachment(
            file=temp_image_path.with_suffix(".png").name, content=b"ddl"
        ),
    )

    await assert_discord(
        app,
        Image("https://example.com/amiya.png"),
        MessageSegment.attachment(file="image", content=b"amiya"),
    )

    image_route.mock(return_value=httpx.Response(404, content=b"amiya"))
    with pytest.raises(RuntimeError, match="Error downloading image"):
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


async def test_extract_message_id(app: App):
    from nonebot.adapters.discord import Bot
    from nonebot import get_driver, on_message
    from nonebot.adapters.discord.api.model import (
        User,
        Snowflake,
        MessageGet,
        MessageType,
    )

    from nonebot_plugin_saa import Text, SupportedAdapters
    from nonebot_plugin_saa.registries import SaaMessageId
    from nonebot_plugin_saa.adapters.discord import DiscordReceipt, DiscordMessageId

    matcher = on_message()

    @matcher.handle()
    async def _(mid: SaaMessageId):
        assert mid == DiscordMessageId(message_id=1234, channel_id=4321)

        receipt = await Text("amiya").send()
        assert isinstance(receipt, DiscordReceipt)
        assert receipt.extract_message_id() == DiscordMessageId(
            message_id=1234, channel_id=4321
        )

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[SupportedAdapters.discord]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **discord_kwargs)
        msg_event = mock_discord_message_event()
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "create_message",
            data={
                "channel_id": 4321,
                "nonce": None,
                "tts": False,
                "allowed_mentions": None,
                "content": "amiya",
            },
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

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.discord)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **discord_kwargs)
        msg_event = mock_discord_message_event()
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "create_message",
            data={
                "channel_id": 4321,
                "nonce": None,
                "tts": False,
                "allowed_mentions": None,
                "content": "123",
            },
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
            data={
                "channel_id": 4321,
                "nonce": None,
                "tts": False,
                "allowed_mentions": None,
                "content": "123",
            },
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


async def test_send_active(app: App):
    from nonebot import get_driver
    from nonebot.adapters.discord.api.model import (
        User,
        Snowflake,
        MessageGet,
        MessageType,
    )

    from nonebot_plugin_saa import Text, SupportedAdapters, TargetDiscordChannel

    async with app.test_api() as ctx:
        adapter_obj = get_driver()._adapters[SupportedAdapters.discord]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **discord_kwargs)

        send_target = TargetDiscordChannel(channel_id=4321)

        ctx.should_call_api(
            "create_message",
            data={
                "channel_id": 4321,
                "nonce": None,
                "tts": False,
                "allowed_mentions": None,
                "content": "123",
            },
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
                content="123",
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
        await Text("123").send_to(send_target, bot)


async def test_receipt(app: App):
    from nonebot import on_message
    from nonebot.adapters.discord import Bot
    from nonebot.adapters.discord.api.model import (
        User,
        Snowflake,
        MessageGet,
        MessageType,
    )

    from nonebot_plugin_saa.adapters.discord import DiscordReceipt
    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters

    returned_message = MessageGet(
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
    )

    matcher = on_message()

    @matcher.handle()
    async def process():
        receipt = await MessageFactory(Text("123")).send()
        assert isinstance(receipt, DiscordReceipt)

        erec = await receipt.edit(content="456")
        assert isinstance(erec, DiscordReceipt)
        assert erec.message_get.id == Snowflake(123411)

        await receipt.pin(reason="test")

        await receipt.unpin(reason="test")

        await receipt.react("👍")

        await receipt.revoke(reason="test")

        assert receipt.raw.id == Snowflake(1234)

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.discord)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **discord_kwargs)
        msg_event = mock_discord_message_event()
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "create_message",
            data={
                "channel_id": 4321,
                "nonce": None,
                "tts": False,
                "allowed_mentions": None,
                "content": "123",
            },
            result=returned_message,
        )

        returned_edited_message = deepcopy(returned_message)
        returned_edited_message.content = "456"
        returned_edited_message.id = Snowflake(123411)
        ctx.should_call_api(
            "edit_message",
            data={
                "channel_id": 4321,
                "message_id": 1234,
                "content": "456",
                "embeds": None,
                "flags": None,
                "allowed_mentions": None,
                "components": None,
                "files": None,
                "attachments": None,
            },
            result=returned_edited_message,
        )

        ctx.should_call_api(
            "pin_message",
            data={
                "channel_id": 4321,
                "message_id": 1234,
                "reason": "test",
            },
        )

        ctx.should_call_api(
            "unpin_message",
            data={
                "channel_id": 4321,
                "message_id": 1234,
                "reason": "test",
            },
        )

        ctx.should_call_api(
            "create_reaction",
            data={
                "channel_id": 4321,
                "message_id": 1234,
                "emoji": "👍",
            },
        )

        ctx.should_call_api(
            "delete_message",
            data={
                "channel_id": 4321,
                "message_id": 1234,
                "reason": "test",
            },
        )


async def test_list_targets(app: App, mocker: MockerFixture):
    from nonebot import get_adapter
    from nonebot.adapters.discord.api.model import (
        Channel,
        Snowflake,
        ChannelType,
        CurrentUserGuild,
    )

    from nonebot_plugin_saa import TargetDiscordChannel
    from nonebot_plugin_saa.auto_select_bot import get_bot, refresh_bots

    mocker.patch("nonebot_plugin_saa.auto_select_bot.inited", True)

    async with app.test_api() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter, **discord_kwargs)

        ctx.should_call_api(
            "get_current_user_guilds",
            data={},
            result=[
                CurrentUserGuild(
                    id=Snowflake(1234),
                    name="test",
                    icon=None,
                    features=[],
                )
            ],
        )

        ctx.should_call_api(
            "get_guild_channels",
            data={"guild_id": 1234},
            result=[
                Channel(
                    id=Snowflake(4321),
                    type=ChannelType.GUILD_TEXT,
                ),
                Channel(
                    id=Snowflake(4322),
                    type=ChannelType.GUILD_TEXT,
                ),
            ],
        )
        await refresh_bots()

        assert get_bot(TargetDiscordChannel(channel_id=4321)) == bot
