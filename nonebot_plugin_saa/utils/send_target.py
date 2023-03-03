import json
from abc import ABC
from typing import Any, Type

from pydantic import BaseModel

from .const import SupportedAdapters

deserializer_map: dict[SupportedAdapters, Type["AbstractSendTarget"]] = {}


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
