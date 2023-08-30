import json
from abc import ABC
from typing import Any, Dict, Type, ClassVar, cast

from nonebot import get_bot
from nonebot.adapters import Bot
from pydantic import BaseModel, ConfigDict

from .const import SupportedAdapters


class Receipt(BaseModel, ABC):
    model_config = ConfigDict(frozen=True, orm_mode=True)

    _deseriazer_map: ClassVar[Dict[SupportedAdapters, Type["Receipt"]]] = {}

    def __init_subclass__(cls) -> None:
        assert isinstance(cls.__fields__["adapter_name"].default, SupportedAdapters)
        cls._deseriazer_map[cls.__fields__["adapter_name"].default] = cls
        return super().__init_subclass__()

    @classmethod
    def deserialize(cls, source: Any) -> "Receipt":
        if isinstance(source, str):
            raw_obj = json.loads(source)
        else:
            raw_obj = source
            assert raw_obj.get("adapter_name")
        adapter_name = cast(
            SupportedAdapters, SupportedAdapters(raw_obj["adapter_name"])
        )
        return cls._deseriazer_map[adapter_name].parse_obj(raw_obj)

    adapter_name: SupportedAdapters
    bot_id: str

    def _get_bot(self) -> Bot:
        return get_bot(self.bot_id)

    async def revoke(self):
        ...

    @property
    def raw(self) -> Any:
        ...
