""" 提供获取 Bot 的方法 """
import random
from collections import defaultdict
from typing import Dict, List, Callable, Awaitable

from nonebot import get_bots
from nonebot.adapters import Bot

from .registries import PlatformTarget, TargetQQGuildDirect
from .utils import NoBotFound, SupportedAdapters, extract_adapter_type

BOT_CACHE: Dict[PlatformTarget, List[Bot]] = defaultdict(list)

ListTargetsFunc = Callable[[Bot], Awaitable[List[PlatformTarget]]]

list_targets_map: Dict[str, ListTargetsFunc] = {}

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

    ```python
    # __init__.py(插件入口)
    require("nonebot_plugin_saa")
    from nonebot_plugin_saa import enable_auto_select_bot
    enable_auto_select_bot()
    ```

    参见：https://send-anything-anywhere.felinae98.cn/usage/send#发送时自动选择bot
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
    for bot in list(get_bots().values()):
        adapter_name = extract_adapter_type(bot)
        if list_targets := list_targets_map.get(adapter_name):
            targets = await list_targets(bot)
            for target in targets:
                BOT_CACHE[target].append(bot)


def get_bot(target: PlatformTarget) -> Bot:
    """获取 Bot"""
    if not inited:
        raise RuntimeError(
            "\n自动选择 Bot 的功能未启用\n"
            "请在 插件入口(__init__.py) 调用:\n"
            "    require('nonebot_plugin_saa')\n"
            "    from nonebot_plugin_saa import enable_auto_select_bot\n"
            "    enable_auto_select_bot()\n"
            "\n参见：https://send-anything-anywhere.felinae98.cn/usage/send#发送时自动选择bot"
        )

    # TODO: 通过更方便的方式判断当前 Target 是否支持
    if isinstance(target, TargetQQGuildDirect):
        raise NotImplementedError("暂不支持私聊")

    bots = BOT_CACHE.get(target)
    if not bots:
        raise NoBotFound()

    return random.choice(bots)
