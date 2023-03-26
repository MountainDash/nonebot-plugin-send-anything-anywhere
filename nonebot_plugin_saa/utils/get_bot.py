""" 提供获取 Bot 的方法 """
import random
from collections import defaultdict
from typing import Callable, Optional, Awaitable

from nonebot.adapters import Bot
from nonebot import get_bots, get_driver

from .const import SupportedAdapters
from .helpers import extract_adapter_type
from .platform_send_target import PlatformTarget, TargetQQGuildDirect

BOT_CACHE: dict[PlatformTarget, list[Bot]] = defaultdict(list)

GetTargetFunc = Callable[[Bot], Awaitable[list[PlatformTarget]]]

get_targets_map: dict[str, GetTargetFunc] = {}


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


driver = get_driver()


@driver.on_bot_connect
@driver.on_bot_disconnect
async def _(bot: Bot):
    await refresh_bots()
