import json
from abc import ABC
from typing import Any, Dict, Type, ClassVar, cast, Union, Optional

from nonebot.adapters import Bot
from pydantic import BaseModel, ConfigDict

from .auto_select_bot import get_bot_by_id
from .const import SupportedAdapters
from .exceptions import AdapterNotSupported



class Receipt(BaseModel, ABC):
    model_config = ConfigDict(frozen=True, orm_mode=True)

    _deserializer_map: ClassVar[Dict[SupportedAdapters, Type["Receipt"]]] = {}

    def __init_subclass__(cls) -> None:
        assert isinstance(cls.__fields__["adapter_name"].default, SupportedAdapters)
        cls._deserializer_map[cls.__fields__["adapter_name"].default] = cls
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
        return cls._deserializer_map[adapter_name].parse_obj(raw_obj)

    message_id: Union[str, int]
    sent_msg: Optional[Any]

    adapter_name: SupportedAdapters
    bot_id: str

    def _get_bot(self) -> Bot:
        bot = get_bot_by_id(self.adapter_name, self.bot_id)
        if not bot:
            raise RuntimeError(
                f"Bot of {self.adapter_name} {self.bot_id} not connected"
            )
        return bot

    async def revoke(self):
        ...

    async def edit(self, msg, at_sender=False, reply=False):
        raise AdapterNotSupported(self._get_bot().adapter.get_name())

    @classmethod
    @property
    def revoke_able(cls):
        return getattr(Receipt, 'revoke') != getattr(cls, 'revoke')

    @classmethod
    @property
    def edit_able(cls):
        return getattr(Receipt, 'edit') != getattr(cls, 'edit')


    @property
    def raw(self) -> Any:
        ...
