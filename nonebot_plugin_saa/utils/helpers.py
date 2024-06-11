from typing import TYPE_CHECKING, TypeVar, cast

from nonebot.internal.adapter.bot import Bot

from .const import SupportedAdapters, supported_adapter_names
from .exceptions import AdapterNotSupported, UnexpectedMessageIdType

if TYPE_CHECKING:
    from nonebot_plugin_saa.registries.message_id import MessageId

TMessageId = TypeVar("TMessageId", bound="type[MessageId]")


def extract_adapter_type(bot: Bot) -> SupportedAdapters:
    adapter_name = bot.adapter.get_name()
    if adapter_name not in supported_adapter_names:
        raise AdapterNotSupported(adapter_name)

    adapter_name = SupportedAdapters(adapter_name)
    return cast(SupportedAdapters, adapter_name)


def type_message_id_check(
    expected_type: TMessageId, message_id: "MessageId"
) -> TMessageId:
    if not isinstance(message_id, expected_type):
        raise UnexpectedMessageIdType(expected_type, message_id)
    return cast(TMessageId, message_id)
