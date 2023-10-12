import json
from abc import ABC
from enum import Enum
from typing import Any, Dict, Generic, TypeVar, ClassVar

from pydantic import BaseModel

KT = TypeVar("KT")  # index key type
ST = TypeVar("ST")  # deserialized type


class Level(Enum):
    MetaBase = 1
    Base = 2
    Normal = 3


class SerializationMeta(BaseModel, ABC, Generic[ST, KT]):
    _index_key: ClassVar[str]
    _deserializer_dict: ClassVar[Dict]
    _level: ClassVar[Level] = Level.MetaBase

    class Config:
        frozen = True
        orm_mode = True

    def __init_subclass__(cls) -> None:
        if cls._level == Level.MetaBase:
            cls._level = Level.Base
            cls._deserializer_dict = {}
        elif cls._level == Level.Base:
            cls._level = Level.Normal
            cls._deserializer_dict[cls.__fields__[cls._index_key].default] = cls
        elif cls._level == Level.Normal:
            pass
        else:
            raise RuntimeError("SerializationMeta init error")

        super().__init_subclass__()

    @classmethod
    def deserialize(cls, source: Any) -> ST:
        if isinstance(source, str):
            raw_obj = json.loads(source)
        else:
            raw_obj = source

        key = raw_obj.get(cls._index_key)
        assert key
        return cls._deserializer_dict[key].parse_obj(raw_obj)
