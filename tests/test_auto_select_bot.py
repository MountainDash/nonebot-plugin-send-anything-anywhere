import asyncio

import pytest
from nonebug import App
from pytest_mock import MockerFixture
from nonebot import get_driver, get_adapter
from nonebot.adapters.qqguild import Bot, Adapter
from nonebot.adapters.qqguild.config import BotInfo


async def test_disable(app: App):
    from nonebot_plugin_saa import TargetQQGuildChannel
    from nonebot_plugin_saa.auto_select_bot import get_bot

    async with app.test_api() as ctx:
        adapter = get_adapter(Adapter)
        ctx.create_bot(
            base=Bot,
            adapter=adapter,
            bot_info=BotInfo(id="3344", token="", secret=""),
        )

        await asyncio.sleep(0.1)

        target = TargetQQGuildChannel(channel_id=2233)

        with pytest.raises(RuntimeError):
            get_bot(target)


async def test_enable(app: App, mocker: MockerFixture):
    from nonebot.adapters.qqguild.api import Guild, Channel

    from nonebot_plugin_saa.auto_select_bot import get_bot
    from nonebot_plugin_saa import TargetQQGuildChannel, enable_auto_select_bot

    # 结束后会自动恢复到原来的状态
    mocker.patch("nonebot_plugin_saa.auto_select_bot.inited", False)

    enable_auto_select_bot()

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
        await asyncio.sleep(0.1)

        target = TargetQQGuildChannel(channel_id=2233)
        assert bot is get_bot(target)

    # 清理
    driver = get_driver()
    driver._bot_connection_hook.clear()
    driver._bot_disconnection_hook.clear()


async def test_send_auto_select(app: App, mocker: MockerFixture):
    from nonebot import get_driver
    from nonebot.adapters.qqguild.api import Guild, Channel, Message

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
        adapter_qqguild = get_driver()._adapters[str(SupportedAdapters.qqguild)]
        ctx.create_bot(
            base=Bot,
            adapter=adapter_qqguild,
            bot_info=BotInfo(id="3344", token="", secret=""),
        )

        ctx.should_call_api("guilds", {}, [Guild(id=1, name="test1")])
        ctx.should_call_api(
            "get_channels", {"guild_id": 1}, [Channel(id=2233, name="test1")]
        )
        await refresh_bots()

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
            result=Message(id="1255124", channel_id=2233),
        )
        target = TargetQQGuildChannel(channel_id=2233)
        await MessageFactory("123").send_to(target)

        target = TargetQQGuildChannel(channel_id=2)
        with pytest.raises(RuntimeError):
            await MessageFactory("123").send_to(target)

    async with app.test_api() as ctx:
        adapter_qqguild = get_driver()._adapters[str(SupportedAdapters.qqguild)]
        bot = ctx.create_bot(
            base=Bot,
            adapter=adapter_qqguild,
            bot_info=BotInfo(id="3344", token="", secret=""),
        )

        ctx.should_call_api("guilds", {}, [Guild(id=1, name="test1")])
        ctx.should_call_api(
            "get_channels", {"guild_id": 1}, [Channel(id=2233, name="test1")]
        )
        await refresh_bots()

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
            result=Message(id="1255124", channel_id=2233),
        )
        ctx.should_call_api(
            "post_messages",
            data={
                "channel_id": 2233,
                "content": "456",
                "embed": None,
                "ark": None,
                "image": None,
                "file_image": None,
                "markdown": None,
                "message_reference": None,
            },
            result=Message(id="1255124", channel_id=2233),
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


async def test_list_target_failed(app: App, mocker: MockerFixture):
    from nonebot_plugin_saa import enable_auto_select_bot
    from nonebot_plugin_saa.auto_select_bot import BOT_CACHE, refresh_bots

    def raise_exception(bot: Bot):
        raise Exception(bot)

    # 结束后会自动恢复到原来的状态
    mocker.patch("nonebot_plugin_saa.auto_select_bot.inited", False)

    enable_auto_select_bot()

    async with app.test_api() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=Bot,
            adapter=adapter,
            bot_info=BotInfo(id="3344", token="", secret=""),
        )

        mocker.patch(
            "nonebot_plugin_saa.auto_select_bot.list_targets_map",
            {Adapter.get_name(): lambda _bot: raise_exception(_bot)},
        )

        await refresh_bots()
        assert bot not in BOT_CACHE

    # 清理
    driver = get_driver()
    driver._bot_connection_hook.clear()
    driver._bot_disconnection_hook.clear()
