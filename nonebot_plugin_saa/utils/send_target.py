import json
from abc import ABC
from typing import Any, Type, Callable

from pydantic import BaseModel
from nonebot.adapters import Event

from .const import SupportedAdapters

Extractor = Callable[[Event], "AbstractSendTarget"]

deserializer_map: dict[SupportedAdapters, Type["AbstractSendTarget"]] = {}
extractor_map: dict[Type[Event], Extractor] = {}


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
