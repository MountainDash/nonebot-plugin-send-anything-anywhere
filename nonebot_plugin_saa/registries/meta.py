import json
from abc import ABC
from enum import Enum
from typing import Any, ClassVar
from typing_extensions import Self

from pydantic import BaseModel
from nonebot.compat import PYDANTIC_V2, ConfigDict, type_validate_python


class Level(Enum):
    MetaBase = 1
    Base = 2
    Normal = 3


class SerializationMeta(BaseModel, ABC):
    _index_key: ClassVar[str]
    _deserializer_dict: ClassVar[dict]
    _level: ClassVar[Level] = Level.MetaBase

    if PYDANTIC_V2:
        model_config = ConfigDict(
            frozen=True,
            from_attributes=True,
        )

        @classmethod
        def __pydantic_init_subclass__(cls, *args, **kwargs) -> None:
            cls._register_subclass(cls.model_fields)

    else:

        class Config:
            frozen = True
            orm_mode = True

        @classmethod
        def __init_subclass__(cls, *args, **kwargs) -> None:
            cls._register_subclass(cls.__fields__)

            super().__init_subclass__(*args, **kwargs)

    @classmethod
    def _register_subclass(cls, fields) -> None:
        if cls._level == Level.MetaBase:
            cls._level = Level.Base
            cls._deserializer_dict = {}
        elif cls._level == Level.Base:
            cls._level = Level.Normal
            cls._deserializer_dict[fields[cls._index_key].default] = cls
        elif cls._level == Level.Normal:
            pass
        else:
            raise RuntimeError("SerializationMeta init error")

    @classmethod
    def deserialize(cls, source: Any) -> Self:
        if isinstance(source, str):
            raw_obj = json.loads(source)
        else:
            raw_obj = source

        key = raw_obj.get(cls._index_key)
        assert key
        return type_validate_python(cls._deserializer_dict[key], raw_obj)
