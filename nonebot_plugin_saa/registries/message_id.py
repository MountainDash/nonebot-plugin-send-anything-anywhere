from abc import ABC
from typing_extensions import Annotated
from typing import Dict, Type, Callable, Optional

from nonebot.adapters import Event
from nonebot.params import Depends

from .meta import SerializationMeta
from ..utils import SupportedAdapters


class MessageId(SerializationMeta, ABC):
    _index_key = "adapter_name"

    adapter_name: SupportedAdapters


MessageIdGetter = Callable[[Event], MessageId]

_get_message_id_dict: Dict[Type[Event], MessageIdGetter] = {}


def register_message_id_getter(event_type: Type[Event]):
    def register(getter: MessageIdGetter):
        _get_message_id_dict[event_type] = getter
        return getter

    return register


def get_message_id(event: Event) -> Optional[MessageId]:
    for event_type in event.__class__.mro():
        if event_type in _get_message_id_dict:
            if not issubclass(event_type, Event):
                break
            return _get_message_id_dict[event_type](event)
    return None


SaaMessageId = Annotated[MessageId, Depends(get_message_id)]
