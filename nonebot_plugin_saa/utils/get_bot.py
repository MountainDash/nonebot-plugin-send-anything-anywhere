""" 提供获取 Bot 的方法 """
import random
from collections import defaultdict
from typing import Callable, Optional, Awaitable

from nonebot import get_bots
from nonebot.adapters import Bot

from .const import SupportedAdapters
from .helpers import extract_adapter_type
from .platform_send_target import PlatformTarget, TargetQQGuildDirect

BOT_CACHE: dict[PlatformTarget, list[Bot]] = defaultdict(list)

GetTargetFunc = Callable[[Bot], Awaitable[list[PlatformTarget]]]

get_targets_map: dict[str, GetTargetFunc] = {}

inited = False


def _register_hook():
    from nonebot import get_driver

    driver = get_driver()

    @driver.on_bot_connect
    @driver.on_bot_disconnect
    async def _(bot: Bot):
        await refresh_bots()


def enable_auto_select_bot():
    """启用自动选择 Bot 的功能

    启用后，发送主动消息时，可不提供 Target，会自动选择一个 Bot 进行发送
    """
    global inited

    if inited:
        return

    _register_hook()
    inited = True


def register_get_targets(adapter: SupportedAdapters):
    def wrapper(func: GetTargetFunc):
        get_targets_map[adapter] = func
        return func

    return wrapper


async def refresh_bots():
    """刷新缓存的 Bot 数据"""
    BOT_CACHE.clear()
    for bot in get_bots().values():
        adapter_name = extract_adapter_type(bot)
        if get_targets := get_targets_map.get(adapter_name):
            targets = await get_targets(bot)
            for target in targets:
                BOT_CACHE[target].append(bot)


def get_bot(target: PlatformTarget) -> Optional[Bot]:
    """获取 Bot"""
    if isinstance(target, TargetQQGuildDirect):
        raise NotImplementedError("暂不支持私聊")

    bots = BOT_CACHE.get(target)
    if not bots:
        return

    return random.choice(bots)
