from nonebot.internal.adapter.bot import Bot

from .exceptions import AdapterNotSupported
from .const import SupportedAdapters, supported_adapter_names


def extract_adapter_type(bot: Bot) -> SupportedAdapters:
    adapter_name = bot.adapter.get_name()
    if adapter_name not in supported_adapter_names:
        raise AdapterNotSupported(adapter_name)

    adapter_name = SupportedAdapters(adapter_name)
    return adapter_name
