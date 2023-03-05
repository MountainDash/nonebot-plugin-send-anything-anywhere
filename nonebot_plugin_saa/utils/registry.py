import json
from abc import ABC
from typing import TYPE_CHECKING, Any, Type, Callable, Optional, Awaitable

from pydantic import BaseModel
from nonebot.adapters import Bot, Event

from .const import SupportedAdapters

if TYPE_CHECKING:
    from .types import MessageFactory

Extractor = Callable[[Event], "AbstractSendTarget"]
Sender = Callable[
    [Bot, "MessageFactory", "AbstractSendTarget", Optional[Event], bool, bool],
    Awaitable[None],
]

deserializer_map: dict[SupportedAdapters, Type["AbstractSendTarget"]] = {}
extractor_map: dict[Type[Event], Extractor] = {}
sender_map: dict[SupportedAdapters, Sender] = {}


class AbstractSendTarget(BaseModel, ABC):
    adapter_type: SupportedAdapters

    def __init_subclass__(cls) -> None:
        assert isinstance(cls.__fields__["adapter_type"].default, SupportedAdapters)
        deserializer_map[cls.__fields__["adapter_type"].default] = cls
        return super().__init_subclass__()

    def arg_dict(self) -> dict[str, Any]:
        return self.dict(exclude={"adapter_type"}, exclude_unset=True)


def deserialize(json_str: str) -> AbstractSendTarget:
    raw_obj = json.loads(json_str)
    adapter_name = SupportedAdapters(raw_obj["adapter_type"])
    return deserializer_map[adapter_name].parse_obj(raw_obj)


def register_target_extractor(event_type: Type[Event]):
    def wrapper(extractor: Extractor):
        extractor_map[event_type] = extractor
        return extractor

    return wrapper


def extract_send_target(event: Event) -> AbstractSendTarget:
    for event_type in event.__class__.mro():
        if event_type in extractor_map.keys():
            if not issubclass(event_type, Event):
                break
            return extractor_map[event_type](event)
    raise RuntimeError(f"event {event.__class__} not supported")


def register_sender(adapter: SupportedAdapters):
    def wrapper(sender: Sender):
        sender_map[adapter] = sender
        return sender

    return wrapper
