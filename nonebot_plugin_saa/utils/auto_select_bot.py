""" 提供获取 Bot 的方法 """
import random
from collections import defaultdict
from typing import Dict, List, Callable, Optional, Awaitable

from nonebot import get_bots
from nonebot import get_driver
from nonebot.adapters import Bot

from .const import SupportedAdapters
from .exceptions import NoBotFound
from .helpers import extract_adapter_type
from .platform_send_target import PlatformTarget, TargetQQGuildDirect

BOT_CACHE: Dict[PlatformTarget, List[Bot]] = defaultdict(list)
BOT_CACHE_DICT: Dict[SupportedAdapters, Dict[str, Bot]] = defaultdict(dict)

ListTargetsFunc = Callable[[Bot], Awaitable[List[PlatformTarget]]]

list_targets_map: Dict[str, ListTargetsFunc] = {}

inited = False

GetBotIdFunc = Callable[[Bot], str]
_bot_id_getter: Dict[SupportedAdapters, GetBotIdFunc] = {}


def _assert_inited():
    if not inited:
        raise RuntimeError("自动选择 Bot 的功能未启用，请先调用 enable_auto_select_bot 启用此功能")


def register_get_bot_id(adapter_name: SupportedAdapters):
    """注册得到 Bot 唯一标示符的方式"""

    def wrapper(func: GetBotIdFunc):
        _bot_id_getter[adapter_name] = func
        return func

    return wrapper


def get_bot_id(bot: Bot) -> str:
    getter = _bot_id_getter.get(extract_adapter_type(bot))
    if not getter:
        raise RuntimeError(f"get bot id of {type(bot)} is not supported")

    return getter(bot)


def get_bot_by_id(adapter_name: SupportedAdapters, id: str) -> Optional[Bot]:
    """通过唯一标示符选择 Bot，需要开启 auto_select_bot"""
    if adapter_name not in _bot_id_getter.keys():
        raise RuntimeError(f"get bot id of {adapter_name} is not supported")
    return BOT_CACHE_DICT[adapter_name].get(id)


driver = get_driver()


@driver.on_bot_connect
@driver.on_bot_disconnect
async def __(bot: Bot):
    await init_bots()


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


def register_list_targets(adapter: SupportedAdapters):
    def wrapper(func: ListTargetsFunc):
        list_targets_map[adapter] = func
        return func

    return wrapper


async def refresh_bots():
    """刷新缓存的 Bot 数据"""
    BOT_CACHE.clear()
    BOT_CACHE_DICT.clear()
    for bot in list(get_bots().values()):
        adapter_name = extract_adapter_type(bot)

        if list_targets := list_targets_map.get(adapter_name):
            targets = await list_targets(bot)
            for target in targets:
                BOT_CACHE[target].append(bot)


async def init_bots():
    """初始化bot_id和bot的对应关系"""
    BOT_CACHE.clear()
    BOT_CACHE_DICT.clear()
    for bot in list(get_bots().values()):
        adapter_name = extract_adapter_type(bot)

        if adapter_name in _bot_id_getter.keys():
            BOT_CACHE_DICT[adapter_name][get_bot_id(bot)] = bot


def get_bot(target: PlatformTarget) -> Bot:
    """获取 Bot"""
    _assert_inited()

    # TODO: 通过更方便的方式判断当前 Target 是否支持
    if isinstance(target, TargetQQGuildDirect):
        raise NotImplementedError("暂不支持私聊")

    bots = BOT_CACHE.get(target)
    if not bots:
        raise NoBotFound()

    return random.choice(bots)
