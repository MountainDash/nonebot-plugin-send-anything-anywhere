import asyncio
from nonebug import App
from nonebot import get_adapter
from nonebot.adapters.qqguild import Bot, Adapter
from nonebot.adapters.qqguild.config import BotInfo


async def test_disable(app: App):
    from nonebot_plugin_saa import TargetQQGuildChannel
    from nonebot_plugin_saa.utils.get_bot import get_bot

    async with app.test_api() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(
            base=Bot,
            adapter=adapter,
            bot_info=BotInfo(id="3344", token="", secret=""),
        )

        await asyncio.sleep(0.1)

        target = TargetQQGuildChannel(channel_id=2233)
        assert get_bot(target) is None


async def test_enable(app: App):
    from nonebot.adapters.qqguild.api import Guild, Channel

    from nonebot_plugin_saa import TargetQQGuildChannel, enable_auto_select_bot
    from nonebot_plugin_saa.utils.get_bot import get_bot

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
