import pytest
from nonebug.app import App

from .utils import assert_ms


async def test_custom_message_segment(app: App):
    from nonebot.adapters.onebot.v11 import Bot as V11Bot
    from nonebot.adapters.onebot.v12 import Bot as V12Bot
    from nonebot.adapters.onebot.v11 import MessageSegment as V11MessageSegment
    from nonebot.adapters.onebot.v12 import MessageSegment as V12MessageSegment

    from nonebot_plugin_saa.utils import SupportedAdapters
    from nonebot_plugin_saa.types.custom_message_segment import Custom

    custom_msf = Custom(
        {
            SupportedAdapters.onebot_v11: V11MessageSegment.text("314159"),
            SupportedAdapters.onebot_v12: lambda bot: V12MessageSegment.text(
                bot.self_id
            ),
        }
    )

    await assert_ms(
        V11Bot,
        SupportedAdapters.onebot_v11,
        app,
        custom_msf,
        V11MessageSegment.text("314159"),
    )
    await assert_ms(
        V12Bot,
        SupportedAdapters.onebot_v12,
        app,
        custom_msf,
        V12MessageSegment.text("123"),
        self_id="123",
        platform="qq",
    )


async def test_custom_message_segment_failed(app: App):
    from nonebot.adapters.onebot.v11 import Bot as V11Bot
    from nonebot.adapters.onebot.v12 import Bot as V12Bot
    from nonebot.adapters.onebot.v11 import MessageSegment as V11MessageSegment
    from nonebot.adapters.onebot.v12 import MessageSegment as V12MessageSegment

    from nonebot_plugin_saa.types.custom_message_segment import Custom
    from nonebot_plugin_saa.utils import SupportedAdapters, AdapterNotSupported

    custom_msf = Custom(
        {
            SupportedAdapters.onebot_v11: V11MessageSegment.text("314159"),
        }
    )

    await assert_ms(
        V11Bot,
        SupportedAdapters.onebot_v11,
        app,
        custom_msf,
        V11MessageSegment.text("314159"),
    )

    with pytest.raises(AdapterNotSupported):
        await assert_ms(
            V12Bot,
            SupportedAdapters.onebot_v12,
            app,
            custom_msf,
            V12MessageSegment.text("314159"),
            self_id="123",
            platform="qq",
        )
