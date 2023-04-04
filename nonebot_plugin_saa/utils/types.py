import asyncio
from abc import ABC
from copy import deepcopy
from warnings import warn
from inspect import signature
from typing_extensions import Self
from typing import (
    Type,
    TypeVar,
    Callable,
    ClassVar,
    Iterable,
    Optional,
    Awaitable,
    cast,
)

from nonebot.matcher import current_bot, current_event
from nonebot.adapters import Bot, Event, Message, MessageSegment

from .auto_select_bot import get_bot
from .const import SupportedAdapters
from .helpers import extract_adapter_type
from .exceptions import FallbackToDefault, AdapterNotInstalled
from .platform_send_target import PlatformTarget, sender_map, extract_target

TMSF = TypeVar("TMSF", bound="MessageSegmentFactory")
TMF = TypeVar("TMF", bound="MessageFactory")
BuildFunc = (
    Callable[[TMSF], MessageSegment | Awaitable[MessageSegment]]
    | Callable[[TMSF, Bot], MessageSegment | Awaitable[MessageSegment]]
)
CustomBuildFunc = (
    Callable[[], MessageSegment | Awaitable[MessageSegment]]
    | Callable[[Bot], MessageSegment | Awaitable[MessageSegment]]
)


async def do_build(
    msf: "MessageSegmentFactory", builder: BuildFunc, bot: Bot
) -> MessageSegment:
    if len(signature(builder).parameters) == 1:
        builder = cast(
            Callable[
                ["MessageSegmentFactory"], MessageSegment | Awaitable[MessageSegment]
            ],
            builder,
        )
        res = builder(msf)
    elif len(signature(builder).parameters) == 2:
        builder = cast(
            Callable[
                ["MessageSegmentFactory", Bot],
                MessageSegment | Awaitable[MessageSegment],
            ],
            builder,
        )
        res = builder(msf, bot)
    else:
        raise RuntimeError()
    if asyncio.iscoroutine(res):
        return await res
    else:
        res = cast(MessageSegment, res)
        return res


async def do_build_custom(builder: CustomBuildFunc, bot: Bot) -> MessageSegment:
    if len(signature(builder).parameters) == 0:
        builder = cast(
            Callable[[], MessageSegment | Awaitable[MessageSegment]],
            builder,
        )
        res = builder()
    elif len(signature(builder).parameters) == 1:
        builder = cast(
            Callable[[Bot], MessageSegment | Awaitable[MessageSegment]],
            builder,
        )
        res = builder(bot)
    else:
        raise RuntimeError()
    if asyncio.iscoroutine(res):
        return await res
    else:
        res = cast(MessageSegment, res)
        return res


class MessageSegmentFactory(ABC):
    _builders: ClassVar[
        dict[
            SupportedAdapters,
            Callable[[Self], MessageSegment | Awaitable[MessageSegment]]
            | Callable[[Self, Bot], MessageSegment | Awaitable[MessageSegment]],
        ]
    ]

    data: dict
    _custom_builders: dict[SupportedAdapters, CustomBuildFunc]

    def _register_custom_builder(
        self, adapter: SupportedAdapters, ms: MessageSegment | CustomBuildFunc
    ):
        if isinstance(ms, MessageSegment):
            self._custom_builders[adapter] = lambda _: ms
        else:
            self._custom_builders[adapter] = ms

    def _get_custom_builder(
        self, adapter: SupportedAdapters
    ) -> Optional[CustomBuildFunc]:
        return self._custom_builders.get(adapter)

    def __init__(self) -> None:
        self._custom_builders = {}

    def __init_subclass__(cls) -> None:
        cls._builders = {}
        return super().__init_subclass__()

    def __eq__(self, other: Self) -> bool:
        return self.data == other.data

    def overwrite(
        self, adapter: SupportedAdapters, ms: MessageSegment | CustomBuildFunc
    ) -> Self:
        "为某个 adapter 重写产生的 MessageSegment 或重写产生 MessageSegment 的方法"
        self._register_custom_builder(adapter, ms)
        return self

    async def build(self, bot: Bot) -> MessageSegment:
        adapter_name = extract_adapter_type(bot)
        if custom_builder := self._get_custom_builder(adapter_name):
            return await do_build_custom(custom_builder, bot)
        if builder := self._builders[adapter_name]:
            return await do_build(self, builder, bot)
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
        warn(DeprecationWarning("MessageFactory.build is deprecated"))
        return await self._build(bot)

    async def _build(self, bot: Bot) -> Message:
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

    async def send(self, *, at_sender=False, reply=False):
        "回复消息，仅能用在事件相应器中"
        try:
            event = current_event.get()
            bot = current_bot.get()
        except LookupError:
            raise RuntimeError("send() 仅能在事件相应器中使用，主动发送消息请使用 send_to")

        target = extract_target(event)
        await self._do_send(bot, target, event, at_sender, reply)

    async def send_to(self, target: PlatformTarget, bot: Bot | None = None):
        if bot is None:
            bot = get_bot(target)
        await self._do_send(bot, target, None, False, False)

    async def _do_send(
        self,
        bot: Bot,
        target: PlatformTarget,
        event: Optional[Event],
        at_sender: bool,
        reply: bool,
    ):
        adapter = extract_adapter_type(bot)
        if not (sender := sender_map[adapter]):
            raise RuntimeError(
                f"send method for {adapter} not registerd"
            )  # pragma: no cover
        await sender(bot, self, target, event, at_sender, reply)


AggregatedSender = Callable[
    [Bot, list[MessageFactory], PlatformTarget, Optional[Event]], Awaitable[None]
]


class AggregatedMessageFactory:
    message_factories: list[MessageFactory]
    sender: ClassVar[dict[SupportedAdapters, AggregatedSender]] = {}

    def __init__(self, msgs: list[MessageFactory | MessageSegmentFactory]) -> None:
        self.message_factories = []
        for msg in msgs:
            if isinstance(msg, MessageSegmentFactory):
                self.message_factories.append(MessageFactory(msg))
            else:
                self.message_factories.append(msg)

    def __eq__(self, other: Self):
        return self.message_factories == other.message_factories

    @classmethod
    def register_aggragated_sender(cls, adapter: SupportedAdapters):
        def wrapper(func: AggregatedSender):
            cls.sender[adapter] = func
            return func

        return wrapper

    async def _send_aggregated_message_default(
        self, bot: Bot, target: PlatformTarget, event: Optional[Event]
    ):
        for msg_fac in self.message_factories:
            await msg_fac._do_send(bot, target, event, False, False)

    async def _do_send(self, bot: Bot, target: PlatformTarget, event: Optional[Event]):
        adapter = extract_adapter_type(bot)
        if sender := self.__class__.sender.get(adapter):  # custom aggregate sender
            try:
                return await sender(bot, self.message_factories, target, event)
            except FallbackToDefault:
                await self._send_aggregated_message_default(bot, target, event)
        # fallback
        await self._send_aggregated_message_default(bot, target, event)

    async def send(self):
        "回复消息，仅能用在事件相应器中"
        try:
            event = current_event.get()
            bot = current_bot.get()
        except LookupError:
            raise RuntimeError("send() 仅能在事件相应器中使用，主动发送消息请使用 send_to")

        target = extract_target(event)
        await self._do_send(bot, target, event)

    async def send_to(self, target: PlatformTarget, bot: Bot | None = None):
        if bot is None:
            bot = get_bot(target)
        await self._do_send(bot, target, None)


def register_ms_adapter(
    adapter: SupportedAdapters, ms_factory: Type[TMSF]
) -> Callable[[BuildFunc], BuildFunc]:
    def decorator(builder: BuildFunc) -> BuildFunc:
        ms_factory._builders[adapter] = builder
        return builder

    return decorator


def assamble_message_factory(
    origin_msg_factory: MessageFactory,
    mention_message_segment: Optional[MessageSegmentFactory],
    reply_message_segment: Optional[MessageSegmentFactory],
    at_sender: bool,
    reply: bool,
) -> MessageFactory:
    full_message_factory = MessageFactory([])
    if reply_message_segment and reply:
        full_message_factory += reply_message_segment
    if mention_message_segment and at_sender:
        full_message_factory += mention_message_segment
    full_message_factory += origin_msg_factory

    return full_message_factory
