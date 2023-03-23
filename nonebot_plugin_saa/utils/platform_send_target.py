import json
from abc import ABC
from typing_extensions import Self
from typing import (
    TYPE_CHECKING,
    Any,
    Type,
    Literal,
    Callable,
    ClassVar,
    Optional,
    Awaitable,
)

from pydantic import BaseModel
from nonebot.adapters import Bot, Event

from .helpers import extract_adapter_type
from .const import SupportedAdapters, SupportedPlatform

if TYPE_CHECKING:
    from .types import MessageFactory


class PlatformTarget(BaseModel, ABC):
    _deseriazer_map: ClassVar[dict[SupportedPlatform, Type["PlatformTarget"]]] = {}
    platform_type: SupportedPlatform

    class Config:
        frozen = True
        orm_mode = True

    def __init_subclass__(cls) -> None:
        assert isinstance(cls.__fields__["platform_type"].default, SupportedPlatform)
        cls._deseriazer_map[cls.__fields__["platform_type"].default] = cls
        return super().__init_subclass__()

    def arg_dict(self, bot: Bot):
        adapter_type = extract_adapter_type(bot)
        if (self.platform_type, adapter_type) not in convert_to_arg_map.keys():
            raise RuntimeError(
                f"PlatformTarget {self.platform_type} not support {adapter_type}"
            )
        return convert_to_arg_map[(self.platform_type, adapter_type)](self)

    @classmethod
    def deserialize(cls, source: str | dict) -> Self:
        if isinstance(source, str):
            raw_obj = json.loads(source)
        else:
            raw_obj = source
            assert raw_obj.get("platform_type")
        platform_type = SupportedPlatform(raw_obj["platform_type"])
        return cls._deseriazer_map[platform_type].parse_obj(raw_obj)


class TargetQQGroup(PlatformTarget):
    """QQ群

    参数
        group_id: 群号
    """

    platform_type: Literal[SupportedPlatform.qq_group] = SupportedPlatform.qq_group
    group_id: int


class TargetQQPrivate(PlatformTarget):
    """QQ私聊

    参数
        user_id: QQ号
    """

    platform_type: Literal[SupportedPlatform.qq_private] = SupportedPlatform.qq_private
    user_id: int


class TargetQQGuildChannel(PlatformTarget):
    """QQ频道子频道

    参数
        channel_id: 子频道号
    """

    platform_type: Literal[
        SupportedPlatform.qq_guild_channel
    ] = SupportedPlatform.qq_guild_channel
    channel_id: int


class TargetQQGuildDirect(PlatformTarget):
    """QQ频道私聊

    参数
        recipient_id: 接收人ID
        source_guild_id: 来自的频道号
    """

    platform_type: Literal[
        SupportedPlatform.qq_guild_direct
    ] = SupportedPlatform.qq_guild_direct
    recipient_id: int
    source_guild_id: int


class TargetOB12Unknow(PlatformTarget):
    """暂未识别的 Onebot v12 发送目标

    参数
        detail_type: "private" or "group" or "channel"
        user_id, group_id, channel_id, guild_id: 同 ob12 定义
    """

    platform_type: Literal[
        SupportedPlatform.unknown_ob12
    ] = SupportedPlatform.unknown_ob12
    detail_type: Literal["private", "group", "channel"]
    user_id: Optional[str] = None
    group_id: Optional[str] = None
    guild_id: Optional[str] = None
    channel_id: Optional[str] = None


ConvertToArg = Callable[[PlatformTarget], dict[str, Any]]
convert_to_arg_map: dict[tuple[SupportedPlatform, SupportedAdapters], ConvertToArg] = {}


def register_convert_to_arg(adapter: SupportedAdapters, platform: SupportedPlatform):
    def wrapper(func: ConvertToArg):
        convert_to_arg_map[(platform, adapter)] = func
        return func

    return wrapper


Extractor = Callable[[Event], PlatformTarget]
extractor_map: dict[Type[Event], Extractor] = {}


def register_target_extractor(event: Type[Event]):
    def wrapper(func: Extractor):
        extractor_map[event] = func
        return func

    return wrapper


def extract_target(event: Event) -> PlatformTarget:
    "从事件中提取出发送目标，如果不能提取就抛出错误"
    for event_type in event.__class__.mro():
        if event_type in extractor_map.keys():
            if not issubclass(event_type, Event):
                break
            return extractor_map[event_type](event)
    raise RuntimeError(f"event {event.__class__} not supported")


def get_target(event: Event) -> PlatformTarget | None:
    "从事件中提取出发送目标，如果不能提取就返回 None"
    try:
        return extract_target(event)
    except RuntimeError:
        pass


Sender = Callable[
    [Bot, "MessageFactory", "PlatformTarget", Optional[Event], bool, bool],
    Awaitable[None],
]

sender_map: dict[SupportedAdapters, Sender] = {}


def register_sender(adapter: SupportedAdapters):
    def wrapper(sender: Sender):
        sender_map[adapter] = sender
        return sender

    return wrapper
