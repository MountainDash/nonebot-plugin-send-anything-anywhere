import asyncio
from abc import ABC
from copy import deepcopy
from inspect import signature
from typing import (
    Dict,
    List,
    Type,
    Union,
    TypeVar,
    Callable,
    ClassVar,
    Iterable,
    NoReturn,
    Optional,
    Awaitable,
    cast,
)
from warnings import warn

from nonebot.adapters import Bot, Event, Message, MessageSegment
from nonebot.exception import PausedException, FinishedException, RejectedException
from nonebot.matcher import current_bot, current_event, current_matcher
from typing_extensions import Self

from .auto_select_bot import get_bot
from .const import SupportedAdapters
from .exceptions import FallbackToDefault, AdapterNotInstalled
from .helpers import extract_adapter_type, extract_editor_adapter_type
from .platform_send_target import PlatformTarget, sender_map, extract_target, MessageTarget, editor_map

TMSF = TypeVar("TMSF", bound="MessageSegmentFactory")
TMF = TypeVar("TMF", bound="MessageFactory")
BuildFunc = Union[
    Callable[[TMSF], Union[MessageSegment, Awaitable[MessageSegment]]],
    Callable[[TMSF, Bot], Union[MessageSegment, Awaitable[MessageSegment]]],
]
CustomBuildFunc = Union[
    Callable[[], Union[MessageSegment, Awaitable[MessageSegment]]],
    Callable[[Bot], Union[MessageSegment, Awaitable[MessageSegment]]],
]


async def do_build(
    msf: "MessageSegmentFactory",
    builder: BuildFunc,
    bot: Bot,
) -> MessageSegment:
    if len(signature(builder).parameters) == 1:
        builder = cast(
            Callable[
                ["MessageSegmentFactory"],
                Union[MessageSegment, Awaitable[MessageSegment]],
            ],
            builder,
        )
        res = builder(msf)
    elif len(signature(builder).parameters) == 2:
        builder = cast(
            Callable[
                ["MessageSegmentFactory", Bot],
                Union[MessageSegment, Awaitable[MessageSegment]],
            ],
            builder,
        )
        res = builder(msf, bot)
    else:
        raise RuntimeError
    if asyncio.iscoroutine(res):
        return await res
    return cast(MessageSegment, res)


async def do_build_custom(builder: CustomBuildFunc, bot: Bot) -> MessageSegment:
    if len(signature(builder).parameters) == 0:
        builder = cast(
            Callable[[], Union[MessageSegment, Awaitable[MessageSegment]]],
            builder,
        )
        res = builder()
    elif len(signature(builder).parameters) == 1:
        builder = cast(
            Callable[[Bot], Union[MessageSegment, Awaitable[MessageSegment]]],
            builder,
        )
        res = builder(bot)
    else:
        raise RuntimeError
    if asyncio.iscoroutine(res):
        return await res
    return cast(MessageSegment, res)


class MessageSegmentFactory(ABC):
    _builders: ClassVar[
        Dict[
            SupportedAdapters,
            Union[
                Callable[[Self], Union[MessageSegment, Awaitable[MessageSegment]]],
                Callable[[Self, Bot], Union[MessageSegment, Awaitable[MessageSegment]]],
            ],
        ]
    ]

    data: dict
    _custom_builders: Dict[SupportedAdapters, CustomBuildFunc]

    def _register_custom_builder(
        self,
        adapter: SupportedAdapters,
        ms: Union[MessageSegment, CustomBuildFunc],
    ):
        if isinstance(ms, MessageSegment):
            self._custom_builders[adapter] = lambda _: ms
        else:
            self._custom_builders[adapter] = ms

    def _get_custom_builder(
        self,
        adapter: SupportedAdapters,
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
        self,
        adapter: SupportedAdapters,
        ms: Union[MessageSegment, CustomBuildFunc],
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

    def __add__(self: TMSF, other: Union[str, TMSF, Iterable[TMSF]]):
        return MessageFactory(self) + other

    def __radd__(self: TMSF, other: Union[str, TMSF, Iterable[TMSF]]):
        return MessageFactory(other) + self

    async def send(self, *, at_sender=False, reply=False):
        "回复消息，仅能用在事件响应器中"
        return await MessageFactory(self).send(at_sender=at_sender, reply=reply)

    async def send_to(self, target: PlatformTarget, bot: Optional[Bot] = None):
        "主动发送消息，将消息发送到 target，如果不传入 bot 将自动选择 bot（此功能需要显式开启）"
        return await MessageFactory(self).send_to(target, bot)

    async def finish(self, *, at_sender=False, reply=False, **kwargs) -> NoReturn:
        """与 `matcher.finish()` 作用相同，仅能用在事件响应器中"""
        await self.send(at_sender=at_sender, reply=reply, **kwargs)
        raise FinishedException

    async def pause(self, *, at_sender=False, reply=False, **kwargs) -> NoReturn:
        """与 `matcher.pause()` 作用相同，仅能用在事件响应器中"""
        await self.send(at_sender=at_sender, reply=reply, **kwargs)
        raise PausedException

    async def reject(self, *, at_sender=False, reply=False, **kwargs) -> NoReturn:
        """与 `matcher.reject()` 作用相同，仅能用在事件响应器中"""
        await self.send(at_sender=at_sender, reply=reply, **kwargs)
        raise RejectedException

    async def reject_arg(
        self, key: str, *, at_sender=False, reply=False, **kwargs
    ) -> NoReturn:
        """与 `matcher.reject_arg()` 作用相同，仅能用在事件响应器中"""
        matcher = current_matcher.get()
        await self.send(at_sender=at_sender, reply=reply, **kwargs)
        await matcher.reject_arg(key)

    async def reject_receive(
        self, key: str, *, at_sender=False, reply=False, **kwargs
    ) -> NoReturn:
        """与 `matcher.reject_receive()` 作用相同，仅能用在事件响应器中"""
        matcher = current_matcher.get()
        await self.send(at_sender=at_sender, reply=reply, **kwargs)
        await matcher.reject_receive(key)


class MessageFactory(List[TMSF]):
    _text_factory: Callable[[str], TMSF]
    _message_registry: Dict[SupportedAdapters, Type[Message]] = {}

    @classmethod
    def register_text_ms(cls, factory: Callable[[str], TMSF]):
        cls._text_factory = factory
        return factory

    @classmethod
    def get_text_factory(cls):
        return cls._text_factory

    @classmethod
    def register_adapter_message(
        cls,
        adapter: SupportedAdapters,
        message_class: Type[Message],
    ):
        cls._message_registry[adapter] = message_class

    async def build(self, bot: Bot) -> Message:
        warn(DeprecationWarning("MessageFactory.build is deprecated"))
        return await self._build(bot)

    async def _build(self, bot: Bot) -> Message:
        adapter_name = extract_adapter_type(bot)
        if message_type := self._message_registry.get(adapter_name):
            ms: List[MessageSegment] = await asyncio.gather(
                *[ms_factory.build(bot) for ms_factory in self],
            )
            return message_type(ms)
        raise AdapterNotInstalled(adapter_name)

    def __init__(self, message: Union[str, Iterable[TMSF], TMSF]):
        super().__init__()

        if message is None:
            return

        if isinstance(message, str):
            self.append(self.get_text_factory()(message))
        elif isinstance(message, MessageSegmentFactory):
            self.append(message)
        elif isinstance(message, Iterable):
            self.extend(message)

    def __add__(self: TMF, other: Union[str, TMSF, Iterable[TMSF]]) -> TMF:
        result = self.copy()
        result += other
        return result

    def __radd__(self: TMF, other: Union[str, TMSF, Iterable[TMSF]]) -> TMF:
        result = self.__class__(other)
        return result + self

    def __iadd__(self: TMF, other: Union[str, TMSF, Iterable[TMSF]]) -> TMF:
        if isinstance(other, str):
            self.append(self.get_text_factory()(other))
        elif isinstance(other, MessageSegmentFactory):
            self.append(other)
        elif isinstance(other, Iterable):
            self.extend(other)

        return self

    def append(self: TMF, obj: Union[str, TMSF]) -> TMF:
        if isinstance(obj, MessageSegmentFactory):
            super().append(obj)
        elif isinstance(obj, str):
            super().append(self.get_text_factory()(obj))

        return self

    def extend(self: TMF, obj: Union[TMF, Iterable[TMSF]]) -> TMF:
        for message_segment_factory in obj:
            self.append(message_segment_factory)

        return self

    def copy(self: TMF) -> TMF:
        return deepcopy(self)

    async def send(self, *, at_sender=False, reply=False):
        """回复消息，仅能用在事件响应器中"""
        try:
            event = current_event.get()
            bot = current_bot.get()
        except LookupError as e:
            raise RuntimeError("send() 仅能在事件响应器中使用，主动发送消息请使用 send_to") from e

        target = extract_target(event)
        return await self._do_send(bot, target, event, at_sender, reply)

    async def send_to(self, target: PlatformTarget, bot: Optional[Bot] = None):
        """主动发送消息，将消息发送到 target，如果不传入 bot 将自动选择 bot（此功能需要显式开启）"""
        if bot is None:
            bot = get_bot(target)
        return await self._do_send(bot, target, None, False, False)

    async def edit(self, message_target: MessageTarget, *, at_sender=False, reply=False):  # noqa: E501
        """编辑消息，仅能用在事件响应器中"""
        try:
            event = current_event.get()
            bot = current_bot.get()
        except LookupError as e:
            raise RuntimeError("send() 仅能在事件响应器中使用，主动发送消息请使用 send_to") from e

        target = extract_target(event)
        return await self._do_edit(bot, target, message_target, event, at_sender, reply)

    async def edit_to(self, message_target: MessageTarget, target: PlatformTarget,
                      bot: Optional[Bot] = None):
        """主动编辑消息，将消息发送到 target，如果不传入 bot 将自动选择 bot（此功能需要显式开启）"""
        if bot is None:
            bot = get_bot(target)
        return await self._do_edit(bot, target, message_target, None, False, False)

    async def finish(self, *, at_sender=False, reply=False, **kwargs) -> NoReturn:
        """与 `matcher.finish()` 作用相同，仅能用在事件响应器中"""
        await self.send(at_sender=at_sender, reply=reply, **kwargs)
        raise FinishedException

    async def pause(self, *, at_sender=False, reply=False, **kwargs) -> NoReturn:
        """与 `matcher.pause()` 作用相同，仅能用在事件响应器中"""
        await self.send(at_sender=at_sender, reply=reply, **kwargs)
        raise PausedException

    async def reject(self, *, at_sender=False, reply=False, **kwargs) -> NoReturn:
        """与 `matcher.reject()` 作用相同，仅能用在事件响应器中"""
        await self.send(at_sender=at_sender, reply=reply, **kwargs)
        raise RejectedException

    async def reject_arg(
        self, key: str, *, at_sender=False, reply=False, **kwargs
    ) -> NoReturn:
        """与 `matcher.reject_arg()` 作用相同，仅能用在事件响应器中"""
        matcher = current_matcher.get()
        await self.send(at_sender=at_sender, reply=reply, **kwargs)
        await matcher.reject_arg(key)

    async def reject_receive(
        self, key: str, *, at_sender=False, reply=False, **kwargs
    ) -> NoReturn:
        """与 `matcher.reject_receive()` 作用相同，仅能用在事件响应器中"""
        matcher = current_matcher.get()
        await self.send(at_sender=at_sender, reply=reply, **kwargs)
        await matcher.reject_receive(key)

    async def _do_send(
        self,
        bot: Bot,
        target: PlatformTarget,
        event: Optional[Event],
        at_sender: bool,
        reply: bool,
    ):
        adapter = extract_adapter_type(bot)
        if not (sender := sender_map.get(adapter)):
            raise RuntimeError(
                f"send method for {adapter} not registered",
            )  # pragma: no cover
        return await sender(bot, self, target, event, at_sender, reply)

    async def _do_edit(
        self,
        bot: Bot,
        target: PlatformTarget,
        message_target: MessageTarget,
        event: Optional[Event],
        at_sender: bool,
        reply: bool,
    ):
        adapter = extract_editor_adapter_type(bot)
        if not (editor := editor_map.get(adapter)):
            raise RuntimeError(
                f"edit method for {adapter} not registered",
            )  # pragma: no cover
        return await editor(bot, self, target, message_target, event, at_sender, reply)


AggregatedSender = Callable[
    [Bot, List[MessageFactory], PlatformTarget, Optional[Event]],
    Awaitable[None],
]


class AggregatedMessageFactory:
    message_factories: List[MessageFactory]
    sender: ClassVar[Dict[SupportedAdapters, AggregatedSender]] = {}

    def __init__(
        self,
        msgs: List[Union[MessageFactory, MessageSegmentFactory]],
    ) -> None:
        self.message_factories = []
        for msg in msgs:
            if isinstance(msg, MessageSegmentFactory):
                self.message_factories.append(MessageFactory(msg))
            else:
                self.message_factories.append(msg)

    def __eq__(self, other: Self):
        return self.message_factories == other.message_factories

    @classmethod
    def register_aggregated_sender(cls, adapter: SupportedAdapters):
        def wrapper(func: AggregatedSender):
            cls.sender[adapter] = func
            return func

        return wrapper

    async def _send_aggregated_message_default(
        self,
        bot: Bot,
        target: PlatformTarget,
        event: Optional[Event],
    ):
        for msg_fac in self.message_factories:
            await msg_fac._do_send(bot, target, event, False, False)  # noqa: SLF001

    async def _do_send(self, bot: Bot, target: PlatformTarget, event: Optional[Event]):
        adapter = extract_adapter_type(bot)
        if sender := self.__class__.sender.get(adapter):  # custom aggregate sender
            try:
                return await sender(bot, self.message_factories, target, event)
            except FallbackToDefault:
                await self._send_aggregated_message_default(bot, target, event)
        # fallback
        await self._send_aggregated_message_default(bot, target, event)
        return None

    async def send(self):
        "回复消息，仅能用在事件响应器中"
        try:
            event = current_event.get()
            bot = current_bot.get()
        except LookupError as e:
            raise RuntimeError("send() 仅能在事件响应器中使用，主动发送消息请使用 send_to") from e

        target = extract_target(event)
        await self._do_send(bot, target, event)

    async def send_to(self, target: PlatformTarget, bot: Optional[Bot] = None):
        "主动发送消息，将消息发送到 target，如果不传入 bot 将自动选择 bot（此功能需要显式开启）"
        if bot is None:
            bot = get_bot(target)
        await self._do_send(bot, target, None)

    async def finish(self, **kwargs) -> NoReturn:
        """与 `matcher.finish()` 作用相同，仅能用在事件响应器中"""
        await self.send(**kwargs)
        raise FinishedException

    async def pause(self, **kwargs) -> NoReturn:
        """与 `matcher.pause()` 作用相同，仅能用在事件响应器中"""
        await self.send(**kwargs)
        raise PausedException

    async def reject(self, **kwargs) -> NoReturn:
        """与 `matcher.reject()` 作用相同，仅能用在事件响应器中"""
        await self.send(**kwargs)
        raise RejectedException

    async def reject_arg(self, key: str, **kwargs) -> NoReturn:
        """与 `matcher.reject_arg()` 作用相同，仅能用在事件响应器中"""
        matcher = current_matcher.get()
        await self.send(**kwargs)
        await matcher.reject_arg(key)

    async def reject_receive(self, key: str, **kwargs) -> NoReturn:
        """与 `matcher.reject_receive()` 作用相同，仅能用在事件响应器中"""
        matcher = current_matcher.get()
        await self.send(**kwargs)
        await matcher.reject_receive(key)


def register_ms_adapter(
    adapter: SupportedAdapters,
    ms_factory: Type[TMSF],
) -> Callable[[BuildFunc], BuildFunc]:
    def decorator(builder: BuildFunc) -> BuildFunc:
        ms_factory._builders[adapter] = builder  # noqa: SLF001
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
