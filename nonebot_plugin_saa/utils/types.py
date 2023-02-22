import asyncio
from abc import ABC
from copy import deepcopy
from inspect import signature
from typing_extensions import Self
from typing import Type, TypeVar, Callable, ClassVar, Iterable, Awaitable, cast

from nonebot.internal.adapter.bot import Bot
from nonebot.internal.adapter.message import Message, MessageSegment

from .const import SupportedAdapters
from .helpers import extract_adapter_type
from .exceptions import AdapterNotInstalled

TMSF = TypeVar("TMSF", bound="MessageSegmentFactory")
TMF = TypeVar("TMF", bound="MessageFactory")


class MessageSegmentFactory(ABC):
    _builders: ClassVar[
        dict[
            SupportedAdapters,
            Callable[[Self], MessageSegment | Awaitable[MessageSegment]]
            | Callable[[Self, Bot], MessageSegment | Awaitable[MessageSegment]],
        ]
    ]

    data: dict

    def __init_subclass__(cls) -> None:
        cls._builders = {}
        return super().__init_subclass__()

    def __eq__(self, other: Self) -> bool:
        return self.data == other.data

    async def build(self, bot: Bot) -> MessageSegment:
        adapter_name = extract_adapter_type(bot)
        if builder := self._builders[adapter_name]:
            if len(signature(builder).parameters) == 1:
                builder = cast(
                    Callable[[Self], MessageSegment | Awaitable[MessageSegment]],
                    builder,
                )
                res = builder(self)
            elif len(signature(builder).parameters) == 2:
                builder = cast(
                    Callable[[Self, Bot], MessageSegment | Awaitable[MessageSegment]],
                    builder,
                )
                res = builder(self, bot)
            else:
                raise RuntimeError()
            if asyncio.iscoroutine(res):
                return await res
            else:
                res = cast(MessageSegment, res)
                return res
        raise AdapterNotInstalled(adapter_name)

    def __add__(self: TMSF, other: str | TMSF | Iterable[TMSF]):
        return MessageFactory(self) + other

    def __radd__(self: TMSF, other: str | TMSF | Iterable[TMSF]):
        return MessageFactory(other) + self


class MessageFactory(list[TMSF]):
    _text_factory: Callable[[str], TMSF]
    _message_registry: dict[SupportedAdapters, type[Message]] = {}

    @classmethod
    def register_text_ms(cls, factory: Callable[[str], TMSF]):
        cls._text_factory = factory
        return factory

    @classmethod
    def get_text_factory(cls):
        return cls._text_factory

    @classmethod
    def register_adapter_message(
        cls, adapter: SupportedAdapters, message_class: type[Message]
    ):
        cls._message_registry[adapter] = message_class

    async def build(self, bot: Bot) -> Message:
        adapter_name = extract_adapter_type(bot)
        if message_type := self._message_registry.get(adapter_name):
            ms: tuple[MessageSegment] = await asyncio.gather(
                *[ms_factory.build(bot) for ms_factory in self]
            )
            return message_type(ms)
        raise AdapterNotInstalled(adapter_name)

    def __init__(self, message: str | Iterable[TMSF] | TMSF):
        super().__init__()

        if message is None:
            return
        elif isinstance(message, str):
            self.append(self.get_text_factory()(message))
        elif isinstance(message, MessageSegmentFactory):
            self.append(message)
        elif isinstance(message, Iterable):
            self.extend(message)

    def __add__(self: TMF, other: str | TMSF | Iterable[TMSF]) -> TMF:
        result = self.copy()
        result += other
        return result

    def __radd__(self: TMF, other: str | TMSF | Iterable[TMSF]) -> TMF:
        result = self.__class__(other)
        return result + self

    def __iadd__(self: TMF, other: str | TMSF | Iterable[TMSF]) -> TMF:
        if isinstance(other, str):
            self.append(self.get_text_factory()(other))
        elif isinstance(other, MessageSegmentFactory):
            self.append(other)
        elif isinstance(other, Iterable):
            self.extend(other)

        return self

    def append(self: TMF, obj: str | TMSF) -> TMF:
        if isinstance(obj, MessageSegmentFactory):
            super().append(obj)
        elif isinstance(obj, str):
            super().append(self.get_text_factory()(obj))

        return self

    def extend(self: TMF, obj: TMF | Iterable[TMSF]) -> TMF:
        for message_segment_factory in obj:
            self.append(message_segment_factory)

        return self

    def copy(self: TMF) -> TMF:
        return deepcopy(self)


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
