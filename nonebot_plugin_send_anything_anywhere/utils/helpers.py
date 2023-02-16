from collections.abc import Awaitable
from typing import Type, TypeVar, Callable

from nonebot.internal.adapter.bot import Bot
from nonebot.internal.adapter.message import MessageSegment

from .const import SupportedAdapters
from .types import MessageSegmentFactory

T = TypeVar("T", bound=MessageSegmentFactory)
BuildFunc = (
    Callable[[T], MessageSegment | Awaitable[MessageSegment]]
    | Callable[[T, Bot], MessageSegment | Awaitable[MessageSegment]]
)


def register_ms_adapter(
    adapter: SupportedAdapters, ms_factory: Type[T]
) -> Callable[[BuildFunc], BuildFunc]:
    def decorator(builder: BuildFunc) -> BuildFunc:
        ms_factory._builders[adapter] = builder
        return builder

    return decorator
