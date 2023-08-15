from nonebot.internal.adapter.bot import Bot

from .const import SupportedAdapters, SupportedEditorAdapters, supported_adapter_names, \
    supported_editor_adapter_names
from .exceptions import AdapterNotSupported


def extract_adapter_type(bot: Bot) -> SupportedAdapters:
    adapter_name = bot.adapter.get_name()
    if adapter_name not in supported_adapter_names:
        raise AdapterNotSupported(adapter_name)

    adapter_name = SupportedAdapters(adapter_name)
    return adapter_name


def extract_editor_adapter_type(bot: Bot) -> SupportedEditorAdapters:
    adapter_name = bot.adapter.get_name()
    if adapter_name not in supported_editor_adapter_names:
        raise AdapterNotSupported(adapter_name)

    adapter_name = SupportedEditorAdapters(adapter_name)
    return adapter_name
