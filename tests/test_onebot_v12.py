from io import BytesIO
from pathlib import Path
from functools import partial

from nonebug import App
from pytest_mock import MockerFixture
from nonebot import get_driver, get_adapter
from nonebot.adapters.onebot.v12 import Bot, Adapter, Message, MessageSegment

from nonebot_plugin_saa.utils import SupportedAdapters
from nonebot_plugin_saa import Text, Image, MessageFactory

from .utils import assert_ms, ob12_kwargs, mock_obv12_message_event

assert_onebot_v12 = partial(
    assert_ms, Bot, SupportedAdapters.onebot_v12, self_id="314159", **ob12_kwargs()
)


async def test_text(app: App):
    await assert_onebot_v12(app, Text("123"), MessageSegment.text("123"))


async def test_image(app: App):
    adapter = get_driver()._adapters[str(SupportedAdapters.onebot_v12)]

    async with app.test_api() as ctx:
        bot = ctx.create_bot(
            base=Bot, adapter=adapter, self_id="314159", **ob12_kwargs()
        )
        ctx.should_call_api(
            "upload_file",
            {"type": "url", "name": "image", "url": "https://example.com/image.png"},
            {"file_id": "123"},
        )
        generated_ms = await Image("https://example.com/image.png").build(bot)
        assert generated_ms == MessageSegment.image("123")

    async with app.test_api() as ctx:
        bot = ctx.create_bot(
            base=Bot, adapter=adapter, self_id="314159", **ob12_kwargs()
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
        bot = ctx.create_bot(
            base=Bot, adapter=adapter, self_id="314159", **ob12_kwargs()
        )

        image_path = Path(__file__).parent / "image.png"

        ctx.should_call_api(
            "upload_file",
            {"type": "path", "name": "image", "path": str(image_path.resolve())},
            {"file_id": "123"},
        )
        generated_ms = await Image(image_path).build(bot)
        assert generated_ms == MessageSegment.image("123")

    async with app.test_api() as ctx:
        bot = ctx.create_bot(
            base=Bot, adapter=adapter, self_id="314159", **ob12_kwargs()
        )

        data = BytesIO(b"\x89PNG\r")

        ctx.should_call_api(
            "upload_file",
            {"type": "data", "name": "image", "data": b"\x89PNG\r"},
            {"file_id": "123"},
        )
        generated_ms = await Image(data).build(bot)
        assert generated_ms == MessageSegment.image("123")


async def test_mention(app: App):
    from nonebot.adapters.onebot.v12 import MessageSegment

    from nonebot_plugin_saa import Mention

    await assert_onebot_v12(app, Mention("123"), MessageSegment.mention("123"))


async def test_reply(app: App):
    from nonebot.adapters.onebot.v12 import MessageSegment

    from nonebot_plugin_saa import Reply

    await assert_onebot_v12(app, Reply("123"), MessageSegment.reply("123"))


async def test_send(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.onebot.v12 import Bot, Message

    from nonebot_plugin_saa import Text, MessageFactory

    matcher = on_message()

    @matcher.handle()
    async def handle():
        await MessageFactory(Text("123")).send()

    async with app.test_matcher(matcher) as ctx:
        ob12_adapter = get_driver()._adapters[str(SupportedAdapters.onebot_v12)]
        bot = ctx.create_bot(base=Bot, adapter=ob12_adapter, **ob12_kwargs())
        message = Message("321")
        message_event = mock_obv12_message_event(message)

        ctx.receive_event(bot, message_event)
        ctx.should_call_api(
            "send_message",
            data={
                "message": Message("123"),
                "detail_type": "private",
                "user_id": message_event.user_id,
            },
            result=None,
        )


async def test_send_active(app: App):
    from nonebot import get_driver

    from nonebot_plugin_saa import TargetQQGroup, TargetQQPrivate, TargetOB12Unknow

    async with app.test_api() as ctx:
        adapter_ob12 = get_driver()._adapters[str(SupportedAdapters.onebot_v12)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_ob12, **ob12_kwargs())

        target = TargetQQGroup(group_id=2233)
        ctx.should_call_api(
            "send_message",
            data={
                "message": Message("123"),
                "detail_type": "group",
                "group_id": "2233",
            },
            result=None,
        )
        await MessageFactory("123").send_to(target, bot)

        target = TargetQQPrivate(user_id=1122)
        ctx.should_call_api(
            "send_message",
            data={
                "message": Message("123"),
                "detail_type": "private",
                "user_id": "1122",
            },
            result=None,
        )
        await MessageFactory("123").send_to(target, bot)

        target = TargetOB12Unknow(detail_type="channel", channel_id="3344")
        ctx.should_call_api(
            "send_message",
            data={
                "message": Message("123"),
                "detail_type": "channel",
                "channel_id": "3344",
                "guild_id": None,
                "user_id": None,
                "group_id": None,
            },
            result=None,
        )
        await MessageFactory("123").send_to(target, bot)


async def test_list_targets(app: App, mocker: MockerFixture):
    from nonebot_plugin_saa.utils.auto_select_bot import get_bot, refresh_bots
    from nonebot_plugin_saa import (
        TargetQQGroup,
        TargetQQPrivate,
        TargetOB12Unknow,
        TargetQQGuildChannel,
    )

    mocker.patch("nonebot_plugin_saa.utils.auto_select_bot.inited", True)

    async with app.test_api() as ctx:
        adapter = get_adapter(Adapter)
        qq_bot = ctx.create_bot(
            base=Bot, adapter=adapter, platform="qq", impl="walle", self_id="1"
        )
        qqguild_bot = ctx.create_bot(
            base=Bot, adapter=adapter, platform="qqguild", impl="all4one", self_id="2"
        )
        unknown_bot = ctx.create_bot(
            base=Bot, adapter=adapter, platform="test", impl="test", self_id="3"
        )

        # QQ
        ctx.should_call_api("get_friend_list", {}, [{"user_id": "1"}])
        ctx.should_call_api("get_group_list", {}, [{"group_id": "2"}])
        ctx.should_call_api("get_guild_list", {}, [])

        # QQGuild
        ctx.should_call_api("get_friend_list", {}, [])
        ctx.should_call_api("get_group_list", {}, [])
        ctx.should_call_api("get_guild_list", {}, [{"guild_id": "1"}])
        ctx.should_call_api(
            "get_channel_list", {"guild_id": "1"}, [{"channel_id": "2"}]
        )

        # Unknown
        ctx.should_call_api("get_friend_list", {}, [{"user_id": "1"}])
        ctx.should_call_api("get_group_list", {}, [{"group_id": "2"}])
        ctx.should_call_api("get_guild_list", {}, [{"guild_id": "3"}])
        ctx.should_call_api(
            "get_channel_list", {"guild_id": "3"}, [{"channel_id": "4"}]
        )
        await refresh_bots()

        send_target_private = TargetQQPrivate(user_id=1)
        assert qq_bot is get_bot(send_target_private)

        send_target_group = TargetQQGroup(group_id=2)
        assert qq_bot is get_bot(send_target_group)

        send_target_qqguild = TargetQQGuildChannel(channel_id=2)
        assert qqguild_bot is get_bot(send_target_qqguild)

        send_private = TargetOB12Unknow(detail_type="private", user_id="1")
        assert unknown_bot is get_bot(send_private)

        send_group = TargetOB12Unknow(detail_type="group", group_id="2")
        assert unknown_bot is get_bot(send_group)

        send_channel = TargetOB12Unknow(
            detail_type="channel", channel_id="4", guild_id="3"
        )
        assert unknown_bot is get_bot(send_channel)
