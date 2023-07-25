from pathlib import Path
from functools import partial

from nonebug import App
from nonebot import get_adapter
from pytest_mock import MockerFixture
from nonebot.adapters.qqguild.api import DMS
from nonebot.adapters.qqguild import Bot, Adapter
from nonebot.adapters.qqguild.config import BotInfo

from nonebot_plugin_saa.utils import SupportedAdapters

from .utils import assert_ms, mock_qqguild_message_event

assert_qqguild = partial(
    assert_ms,
    Bot,
    SupportedAdapters.qqguild,
    self_id="314159",
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


async def test_send(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.qqguild import Bot, Message

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters

    matcher = on_message()

    @matcher.handle()
    async def handle():
        await MessageFactory(Text("123")).send()

    async with app.test_matcher(matcher) as ctx:
        qqguild_adapter = get_driver()._adapters[SupportedAdapters.qqguild]
        bot = ctx.create_bot(
            base=Bot,
            adapter=qqguild_adapter,
            bot_info=BotInfo(id="3344", token="", secret=""),
        )
        event = mock_qqguild_message_event(Message("321"))
        ctx.receive_event(bot, event)
        ctx.should_call_api(
            "post_messages",
            data={
                "channel_id": event.channel_id,
                "msg_id": event.id,
                "content": "123",
                "embed": None,
                "ark": None,
                "image": None,
                "file_image": None,
                "markdown": None,
                "message_reference": None,
            },
            result=None,
        )

        event = mock_qqguild_message_event(Message("322"), direct=True)
        ctx.receive_event(bot, event)
        ctx.should_call_api(
            "post_dms_messages",
            data={
                "guild_id": event.guild_id,
                "msg_id": event.id,
                "content": "123",
                "embed": None,
                "ark": None,
                "image": None,
                "file_image": None,
                "markdown": None,
                "message_reference": None,
            },
            result=None,
        )


async def test_send_active(app: App):
    from nonebot import get_driver

    from nonebot_plugin_saa import (
        MessageFactory,
        TargetQQGuildDirect,
        TargetQQGuildChannel,
    )

    async with app.test_api() as ctx:
        adapter_qqguild = get_driver()._adapters[str(SupportedAdapters.qqguild)]
        bot = ctx.create_bot(
            base=Bot,
            adapter=adapter_qqguild,
            bot_info=BotInfo(id="3344", token="", secret=""),
        )

        ctx.should_call_api(
            "post_messages",
            data={
                "channel_id": 2233,
                "content": "123",
                "embed": None,
                "ark": None,
                "image": None,
                "file_image": None,
                "markdown": None,
                "message_reference": None,
            },
            result=None,
        )
        target = TargetQQGuildChannel(channel_id=2233)
        await MessageFactory("123").send_to(target, bot)

        target = TargetQQGuildDirect(recipient_id=1111, source_guild_id=2222)
        ctx.should_call_api(
            "post_dms",
            data={
                "recipient_id": "1111",
                "source_guild_id": "2222",
            },
            result=DMS(guild_id=3333),
        )
        ctx.should_call_api(
            "post_dms_messages",
            data={
                "guild_id": 3333,
                "content": "123",
                "embed": None,
                "ark": None,
                "image": None,
                "file_image": None,
                "markdown": None,
                "message_reference": None,
            },
            result=None,
        )
        await MessageFactory("123").send_to(target, bot)


async def test_list_targets(app: App, mocker: MockerFixture):
    from nonebot.adapters.qqguild.api import Guild, Channel

    from nonebot_plugin_saa import TargetQQGuildChannel
    from nonebot_plugin_saa.utils.auto_select_bot import get_bot, refresh_bots

    mocker.patch("nonebot_plugin_saa.utils.auto_select_bot.inited", True)

    async with app.test_api() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=Bot,
            adapter=adapter,
            bot_info=BotInfo(id="3344", token="", secret=""),
        )

        ctx.should_call_api("guilds", {}, [Guild(id=1, name="test1")])
        ctx.should_call_api(
            "get_channels", {"guild_id": 1}, [Channel(id=2233, name="test1")]
        )
        await refresh_bots()

        target = TargetQQGuildChannel(channel_id=2233)
        assert bot is get_bot(target)
