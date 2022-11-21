from typing import Type, TypeVar, Callable

from nonebot.internal.adapter.bot import Bot
from nonebot.internal.adapter.message import MessageSegment

from .const import SupportedAdapters
from .types import MessageSegmentFactory

T = TypeVar("T", bound=MessageSegmentFactory)
ConverterFunc = Callable[[T], MessageSegment] | Callable[[T, Bot], MessageSegment]


def register_ms_adapter(
    adapter: SupportedAdapters, ms_factory: Type[T]
) -> Callable[[ConverterFunc], ConverterFunc]:
    def decorator(converter: ConverterFunc) -> ConverterFunc:
        ms_factory._converters[adapter] = converter
        return converter

    return decorator
