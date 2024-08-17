import asyncio
from datetime import datetime
from functools import partial

import pytest

pytest.importorskip("nonebot.adapters.qq")
from nonebug import App
from pytest_mock import MockerFixture
from nonebot import get_driver, get_adapter
from nonebot.adapters.qq import Bot, Adapter
from nonebot.adapters.qq.config import BotInfo
from nonebot.adapters.qq.models import User, Guild, Channel, Message

MockGuild = partial(
    Guild,
    id="1",
    name="test1",
    icon="",
    owner_id="1",
    owner=True,
    member_count=1,
    max_members=1,
    description="",
    joined_at=datetime(2023, 10, 20),
)
MockChannel = partial(
    Channel,
    id="2233",
    guild_id="0",
    name="test1",
    type=0,
    sub_type=0,
    position=0,
    private_type=0,
    speak_permission=0,
)
MockMessage = partial(
    Message, id="1", channel_id="2233", guild_id="1", author=User(id="1")
)


async def test_disable(app: App):
    from nonebot_plugin_saa import TargetQQGuildChannel
    from nonebot_plugin_saa.auto_select_bot import get_bot

    async with app.test_api() as ctx:
        adapter = get_adapter(Adapter)
        ctx.create_bot(
            base=Bot,
            adapter=adapter,
            self_id="3344",
            bot_info=BotInfo(id="3344", token="", secret=""),
        )

        await asyncio.sleep(0.1)

        target = TargetQQGuildChannel(channel_id=2233)

        with pytest.raises(RuntimeError):
            get_bot(target)


async def test_enable(app: App, mocker: MockerFixture):
    from nonebot_plugin_saa.auto_select_bot import get_bot
    from nonebot_plugin_saa import (
        TargetQQGroupOpenId,
        TargetQQGuildChannel,
        TargetQQPrivateOpenId,
        enable_auto_select_bot,
    )

    # 结束后会自动恢复到原来的状态
    mocker.patch("nonebot_plugin_saa.auto_select_bot.inited", False)

    enable_auto_select_bot()

    async with app.test_api() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=Bot,
            adapter=adapter,
            self_id="3344",
            bot_info=BotInfo(id="3344", token="", secret=""),
        )

        ctx.should_call_api("guilds", {}, [MockGuild(id="1", name="test1")])
        ctx.should_call_api(
            "get_channels", {"guild_id": "1"}, [MockChannel(id="2233", name="test1")]
        )
        await asyncio.sleep(0.1)

        target = TargetQQGuildChannel(channel_id=2233)
        assert bot is get_bot(target)

        target = TargetQQGroupOpenId(bot_id="3344", group_openid="GROUP")
        assert bot is get_bot(target)

        target = TargetQQPrivateOpenId(bot_id="3344", user_openid="USER")
        assert bot is get_bot(target)

    # 清理
    driver = get_driver()
    driver._bot_connection_hook.clear()
    driver._bot_disconnection_hook.clear()


async def test_send_auto_select(app: App, mocker: MockerFixture):
    from nonebot import get_driver

    from nonebot_plugin_saa.auto_select_bot import refresh_bots
    from nonebot_plugin_saa import (
        Text,
        MessageFactory,
        SupportedAdapters,
        TargetQQGuildChannel,
        AggregatedMessageFactory,
    )

    mocker.patch("nonebot_plugin_saa.auto_select_bot.inited", True)

    async with app.test_api() as ctx:
        adapter_qqguild = get_driver()._adapters[str(SupportedAdapters.qq)]
        ctx.create_bot(
            base=Bot,
            adapter=adapter_qqguild,
            self_id="3344",
            bot_info=BotInfo(id="3344", token="", secret=""),
        )

        ctx.should_call_api("guilds", {}, [MockGuild(id="1", name="test1")])
        ctx.should_call_api(
            "get_channels", {"guild_id": "1"}, [MockChannel(id="2233", name="test1")]
        )
        await refresh_bots()

        ctx.should_call_api(
            "post_messages",
            data={
                "channel_id": "2233",
                "msg_id": None,
                "event_id": None,
                "content": "123",
            },
            result=MockMessage(id="1255124", channel_id="2233"),
        )
        target = TargetQQGuildChannel(channel_id=2233)
        await MessageFactory("123").send_to(target)

        target = TargetQQGuildChannel(channel_id=2)
        with pytest.raises(RuntimeError):
            await MessageFactory("123").send_to(target)

    async with app.test_api() as ctx:
        adapter_qqguild = get_driver()._adapters[str(SupportedAdapters.qq)]
        bot = ctx.create_bot(
            base=Bot,
            adapter=adapter_qqguild,
            self_id="3344",
            bot_info=BotInfo(id="3344", token="", secret=""),
        )

        ctx.should_call_api("guilds", {}, [MockGuild(id="1", name="test1")])
        ctx.should_call_api(
            "get_channels", {"guild_id": "1"}, [MockChannel(id="2233", name="test1")]
        )
        await refresh_bots()

        ctx.should_call_api(
            "post_messages",
            data={
                "channel_id": "2233",
                "msg_id": None,
                "event_id": None,
                "content": "123",
            },
            result=MockMessage(id="1255124", channel_id="2233"),
        )
        ctx.should_call_api(
            "post_messages",
            data={
                "channel_id": "2233",
                "msg_id": None,
                "event_id": None,
                "content": "456",
            },
            result=MockMessage(id="1255124", channel_id="2233"),
        )

        target = TargetQQGuildChannel(channel_id=2233)
        await AggregatedMessageFactory([Text("123"), Text("456")]).send_to(target)

        target = TargetQQGuildChannel(channel_id=2)
        with pytest.raises(RuntimeError):
            await MessageFactory("123").send_to(target)

        adapter_qqguild.bot_disconnect(bot)

        await refresh_bots()

        target = TargetQQGuildChannel(channel_id=2233)
        with pytest.raises(RuntimeError):
            await AggregatedMessageFactory([Text("123"), Text("456")]).send_to(target)

        # should connect back
        adapter_qqguild.bot_connect(bot)
