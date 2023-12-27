import asyncio
from abc import ABC
from copy import deepcopy
from warnings import warn
from inspect import signature
from typing_extensions import Self
from dataclasses import field, asdict, dataclass
from typing import (
    Any,
    Dict,
    List,
    Type,
    Tuple,
    Union,
    TypeVar,
    Callable,
    ClassVar,
    Iterable,
    NoReturn,
    Optional,
    Awaitable,
    SupportsIndex,
    cast,
    overload,
)

from nonebot.adapters import Bot, Event, Message, MessageSegment
from nonebot.matcher import current_bot, current_event, current_matcher
from nonebot.exception import PausedException, FinishedException, RejectedException

from .auto_select_bot import get_bot
from .registries import Receipt, PlatformTarget, sender_map, extract_target
from .utils import (
    FallbackToDefault,
    SupportedAdapters,
    AdapterNotInstalled,
    extract_adapter_type,
)

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


@dataclass
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

    type: str
    data: Dict[str, Any] = field(default_factory=dict)
    _custom_builders: Dict[SupportedAdapters, CustomBuildFunc] = field(
        init=False, default_factory=dict
    )

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

    def __str__(self) -> str:
        kwstr = ",".join(f"{k}={v!r}" for k, v in self.data.items())
        return f"[SAA:{self.type}|{kwstr}]"

    def __repr__(self) -> str:
        kwrepr = ", ".join(f"{k}={v!r}" for k, v in self.data.items())
        return f"{self.__class__.__name__}({kwrepr})"

    def __len__(self) -> int:
        return len(self.data)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, MessageSegmentFactory):
            return self.data == other.data
        elif isinstance(other, str):
            return self.data == {"text": other}
        return False

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

    def __add__(
        self,
        other: "str | MessageSegmentFactory | Iterable[str | MessageSegmentFactory]",
    ) -> "MessageFactory":
        return MessageFactory(self) + other

    def __radd__(
        self,
        other: "str | MessageSegmentFactory | Iterable[str | MessageSegmentFactory]",
    ) -> "MessageFactory":
        return MessageFactory(other) + self

    async def send(self, *, at_sender=False, reply=False):
        "回复消息，仅能用在事件响应器中"
        return await MessageFactory(self).send(at_sender=at_sender, reply=reply)

    async def send_to(self, target: PlatformTarget, bot: Optional[Bot] = None):
        """主动发送消息，将消息发送到 target，如果不传入 bot 将自动选择 bot

        此功能需要显式开启:

        ```python
        from nonebot_plugin_saa import enable_auto_select_bot
        enable_auto_select_bot()
        ```

        参见：https://send-anything-anywhere.felinae98.cn/usage/send#发送时自动选择bot
        """
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

    def copy(self) -> Self:
        """深拷贝"""
        return deepcopy(self)

    def _asdict(self):
        _dict = asdict(self)
        return {k: v for k, v in _dict.items() if not k.startswith("_")}

    def get(self, key: str, default: Any = None):
        return asdict(self).get(key, default)

    def keys(self):
        return self._asdict().keys()

    def values(self):
        return self._asdict().values()

    def items(self):
        return self._asdict().items()

    def join(
        self, iterable: "Iterable[MessageSegmentFactory | MessageFactory]"
    ) -> "MessageFactory":
        return MessageFactory(self).join(iterable)


class MessageFactory(List[MessageSegmentFactory]):
    _text_factory: Callable[[str], MessageSegmentFactory]
    _message_registry: Dict[SupportedAdapters, Type[Message]] = {}

    @classmethod
    def register_text_ms(cls, factory: Callable[[str], MessageSegmentFactory]):
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

    def __init__(
        self,
        message: "str | MessageSegmentFactory | Iterable[str | MessageSegmentFactory] | None" = None,  # noqa: E501
    ):
        super().__init__()

        if message is None:
            return

        if isinstance(message, str):
            self.append(self.get_text_factory()(message))
        elif isinstance(message, MessageSegmentFactory):
            self.append(message)
        elif isinstance(message, Iterable):
            self.extend(message)

    def __add__(
        self: TMF,
        other: "str | MessageSegmentFactory | Iterable[str | MessageSegmentFactory]",
    ) -> TMF:
        result = self.copy()
        result += other
        return result

    def __radd__(
        self: TMF,
        other: "str | MessageSegmentFactory | Iterable[str | MessageSegmentFactory]",
    ) -> TMF:
        result = self.__class__(other)
        return result + self

    def __iadd__(
        self: TMF,
        other: "str | MessageSegmentFactory | Iterable[str | MessageSegmentFactory]",
    ) -> TMF:
        if isinstance(other, str):
            self.append(self.get_text_factory()(other))
        elif isinstance(other, MessageSegmentFactory):
            self.append(other)
        elif isinstance(other, Iterable):
            self.extend(other)

        return self

    def append(self: TMF, obj: Union[str, MessageSegmentFactory]) -> TMF:
        if isinstance(obj, MessageSegmentFactory):
            super().append(obj)
        elif isinstance(obj, str):
            super().append(self.get_text_factory()(obj))

        return self

    def extend(
        self: TMF, obj: Union[TMF, Iterable[Union[str, MessageSegmentFactory]]]
    ) -> TMF:
        for message_segment_factory in obj:
            self.append(message_segment_factory)

        return self

    def copy(self) -> Self:
        return deepcopy(self)

    def join(self, iterable: "Iterable[MessageSegmentFactory | Self]") -> Self:
        """将多个消息连接并将自身作为分割

        参数:
            iterable: 要连接的消息

        返回:
            连接后的消息
        """
        ret = self.__class__()
        for index, msg in enumerate(iterable):
            if index != 0:
                ret.extend(self)
            if isinstance(msg, MessageSegmentFactory):
                ret.append(msg.copy())
            else:
                ret.extend(msg.copy())
        return ret

    def __str__(self) -> str:
        return "".join(str(ms_factory) for ms_factory in self)

    async def send(self, *, at_sender=False, reply=False) -> "Receipt":
        "回复消息，仅能用在事件响应器中"
        try:
            event = current_event.get()
            bot = current_bot.get()
        except LookupError as e:
            raise RuntimeError("send() 仅能在事件响应器中使用，主动发送消息请使用 send_to") from e

        target = extract_target(event, bot)
        return await self._do_send(bot, target, event, at_sender, reply)

    async def send_to(
        self, target: PlatformTarget, bot: Optional[Bot] = None
    ) -> "Receipt":
        """主动发送消息，将消息发送到 target，如果不传入 bot 将自动选择 bot

        此功能需要显式开启:

        ```python
        from nonebot_plugin_saa import enable_auto_select_bot
        enable_auto_select_bot()
        ```

        参见：https://send-anything-anywhere.felinae98.cn/usage/send#发送时自动选择bot
        """
        if bot is None:
            bot = get_bot(target)
        return await self._do_send(bot, target, None, False, False)

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
    ) -> "Receipt":
        adapter = extract_adapter_type(bot)
        if not (sender := sender_map.get(adapter)):
            raise RuntimeError(
                f"send method for {adapter} not registered",
            )  # pragma: no cover
        return await sender(bot, self, target, event, at_sender, reply)

    @overload
    def __getitem__(self, args: str) -> Self:
        """获取仅包含指定消息段类型的消息

        参数:
            args: 消息段类型

        返回:
            所有类型为 `args` 的消息段
        """

    @overload
    def __getitem__(self, args: Tuple[str, int]) -> MessageSegmentFactory:
        """索引指定类型的消息段

        参数:
            args: 消息段类型和索引

        返回:
            类型为 `args[0]` 的消息段第 `args[1]` 个
        """

    @overload
    def __getitem__(self, args: Tuple[str, slice]) -> Self:
        """切片指定类型的消息段

        参数:
            args: 消息段类型和切片

        返回:
            类型为 `args[0]` 的消息段切片 `args[1]`
        """

    @overload
    def __getitem__(self, args: int) -> MessageSegmentFactory:
        """索引消息段

        参数:
            args: 索引

        返回:
            第 `args` 个消息段
        """

    @overload
    def __getitem__(self, args: slice) -> Self:
        """切片消息段

        参数:
            args: 切片

        返回:
            消息切片 `args`
        """

    def __getitem__(
        self,
        args: Union[
            str,
            Tuple[str, int],
            Tuple[str, slice],
            int,
            slice,
        ],
    ) -> Union[MessageSegmentFactory, Self]:
        arg1, arg2 = args if isinstance(args, tuple) else (args, None)
        if isinstance(arg1, int) and arg2 is None:
            return super().__getitem__(arg1)
        elif isinstance(arg1, slice) and arg2 is None:
            return self.__class__(super().__getitem__(arg1))
        elif isinstance(arg1, str) and arg2 is None:
            return self.__class__(seg for seg in self if seg.type == arg1)
        elif isinstance(arg1, str) and isinstance(arg2, int):
            return [seg for seg in self if seg.type == arg1][arg2]
        elif isinstance(arg1, str) and isinstance(arg2, slice):
            return self.__class__([seg for seg in self if seg.type == arg1][arg2])
        else:
            raise ValueError("Incorrect arguments to slice")  # pragma: no cover

    def __contains__(self, value: Union[MessageSegmentFactory, str]) -> bool:
        """检查消息段是否存在

        参数:
            value: 消息段或消息段类型
        返回:
            消息内是否存在给定消息段或给定类型的消息段
        """
        if isinstance(value, str):
            return bool(next((seg for seg in self if seg.type == value), None))
        return super().__contains__(value)

    def has(self, value: Union[MessageSegmentFactory, str]) -> bool:
        """与 {ref}``__contains__` <nonebot.adapters.Message.__contains__>` 相同"""
        return value in self

    def index(
        self, value: Union[MessageSegmentFactory, str], *args: SupportsIndex
    ) -> int:
        """索引消息段

        参数:
            value: 消息段或者消息段类型
            arg: start 与 end

        返回:
            索引 index

        异常:
            ValueError: 消息段不存在
        """
        if isinstance(value, str):
            first_segment = next((seg for seg in self if seg.type == value), None)
            if first_segment is None:
                raise ValueError(f"Segment with type {value!r} is not in message")
            return super().index(first_segment, *args)
        return super().index(value, *args)

    def get(self, type_: str, count: Optional[int] = None):
        """获取指定类型的消息段

        参数:
            type_: 消息段类型
            count: 获取个数

        返回:
            构建的新消息
        """
        if count is None:
            return self[type_]

        iterator, filtered = (
            seg for seg in self if seg.type == type_
        ), self.__class__()
        for _ in range(count):
            seg = next(iterator, None)
            if seg is None:
                break
            filtered.append(seg)
        return filtered

    def count(self, value: Union[MessageSegmentFactory, str]) -> int:
        """计算指定消息段的个数

        参数:
            value: 消息段或消息段类型

        返回:
            个数
        """
        return len(self[value]) if isinstance(value, str) else super().count(value)

    def only(self, value: Union[MessageSegmentFactory, str]) -> bool:
        """检查消息中是否仅包含指定消息段

        参数:
            value: 指定消息段或消息段类型

        返回:
            是否仅包含指定消息段
        """
        if isinstance(value, str):
            return all(seg.type == value for seg in self)
        return all(seg == value for seg in self)

    def include(self, *types: str) -> Self:
        """过滤消息

        参数:
            types: 包含的消息段类型

        返回:
            新构造的消息
        """
        return self.__class__(seg for seg in self if seg.type in types)

    def exclude(self, *types: str) -> Self:
        """过滤消息

        参数:
            types: 不包含的消息段类型

        返回:
            新构造的消息
        """
        return self.__class__(seg for seg in self if seg.type not in types)


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

        target = extract_target(event, bot)
        await self._do_send(bot, target, event)

    async def send_to(self, target: PlatformTarget, bot: Optional[Bot] = None):
        """主动发送消息，将消息发送到 target，如果不传入 bot 将自动选择 bot

        此功能需要显式开启:

        ```python
        from nonebot_plugin_saa import enable_auto_select_bot
        enable_auto_select_bot()
        ```

        参见：https://send-anything-anywhere.felinae98.cn/usage/send#发送时自动选择bot
        """
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
