import inspect
from typing_extensions import Annotated
from typing import (
    TYPE_CHECKING,
    Any,
    Dict,
    Type,
    Tuple,
    Union,
    Literal,
    Callable,
    ClassVar,
    Optional,
    Awaitable,
)

from pydantic import BaseModel
from nonebot.params import Depends
from nonebot.adapters import Bot, Event
from nonebot.compat import PYDANTIC_V2, ConfigDict

from .meta import SerializationMeta
from ..utils import SupportedAdapters, SupportedPlatform, extract_adapter_type

if TYPE_CHECKING:
    from .receipt import Receipt
    from ..abstract_factories import MessageFactory


class PlatformTarget(SerializationMeta):
    _index_key = "platform_type"

    platform_type: SupportedPlatform

    if PYDANTIC_V2:
        model_config = ConfigDict(
            frozen=True,
            from_attributes=True,
        )
    else:

        class Config:
            frozen = True
            orm_mode = True

    def arg_dict(self, bot: Bot):
        adapter_type = extract_adapter_type(bot)
        if (self.platform_type, adapter_type) not in convert_to_arg_map.keys():
            raise RuntimeError(
                f"PlatformTarget {self.platform_type} not support {adapter_type}",
            )
        return convert_to_arg_map[(self.platform_type, adapter_type)](self)


class BotSpecifier(BaseModel):
    bot_id: str


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


class TargetQQGroupOpenId(PlatformTarget, BotSpecifier):
    """QQ群（open_id）

    参数
        group_openid: 群 open_id
    """

    platform_type: Literal[
        SupportedPlatform.qq_group_openid
    ] = SupportedPlatform.qq_group_openid
    group_openid: str


class TargetQQPrivateOpenId(PlatformTarget, BotSpecifier):
    """QQ私聊（open_id）

    参数
        user_openid: 用户 open_id
    """

    platform_type: Literal[
        SupportedPlatform.qq_private_openid
    ] = SupportedPlatform.qq_private_openid
    user_openid: str


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
    platform: str
    detail_type: Literal["private", "group", "channel"]
    user_id: Optional[str] = None
    group_id: Optional[str] = None
    guild_id: Optional[str] = None
    channel_id: Optional[str] = None


class TargetSatoriUnknown(PlatformTarget):
    """暂未识别的 Satori 发送目标

    参数
        platform: 平台名
        user_id: 用户 ID
        guild_id: 群组 ID
        channel_id: 频道 ID
    """

    platform_type: Literal[
        SupportedPlatform.unknown_satori
    ] = SupportedPlatform.unknown_satori
    platform: str
    user_id: Optional[str] = None
    guild_id: Optional[str] = None
    channel_id: Optional[str] = None


class TargetKaiheilaChannel(PlatformTarget):
    """开黑啦频道

    参数
        channel_id: 频道ID
    """

    platform_type: Literal[
        SupportedPlatform.kaiheila_channel
    ] = SupportedPlatform.kaiheila_channel
    channel_id: str


class TargetKaiheilaPrivate(PlatformTarget):
    """开黑啦私聊

    参数
        user_id: 接收人ID
    """

    platform_type: Literal[
        SupportedPlatform.kaiheila_private
    ] = SupportedPlatform.kaiheila_private
    user_id: str


class TargetTelegramCommon(PlatformTarget):
    """Telegram 普通对话

    参数
        user_id: 对话ID
    """

    platform_type: Literal[
        SupportedPlatform.telegram_common
    ] = SupportedPlatform.telegram_common
    chat_id: Union[int, str]


class TargetTelegramForum(PlatformTarget):
    """Telegram 频道

    参数
        chat_id: 频道ID
        message_thread_id: 板块ID
    """

    platform_type: Literal[
        SupportedPlatform.telegram_forum
    ] = SupportedPlatform.telegram_forum
    chat_id: int
    message_thread_id: int


class TargetFeishuPrivate(PlatformTarget):
    """飞书私聊

    参数
        open_id: 用户 Open ID
    """

    platform_type: Literal[
        SupportedPlatform.feishu_private
    ] = SupportedPlatform.feishu_private
    open_id: str


class TargetFeishuGroup(PlatformTarget):
    """飞书群聊

    参数
        chat_id: 群 ID
    """

    platform_type: Literal[
        SupportedPlatform.feishu_group
    ] = SupportedPlatform.feishu_group
    chat_id: str


class TargetDoDoChannel(PlatformTarget):
    """DoDo Channel

    参数
        channel_id: 频道ID
        dodo_source_id: 用户 ID(可选)
    """

    platform_type: Literal[
        SupportedPlatform.dodo_channel
    ] = SupportedPlatform.dodo_channel
    channel_id: str
    dodo_source_id: Optional[str] = None


class TargetDoDoPrivate(PlatformTarget):
    """DoDo Private

    参数
        dodo_source_id: 用户 ID
        island_source_id: 群 ID
    """

    platform_type: Literal[
        SupportedPlatform.dodo_private
    ] = SupportedPlatform.dodo_private
    island_source_id: str
    dodo_source_id: str


# this union type is for deserialize pydantic model with nested PlatformTarget
AllSupportedPlatformTarget = Union[
    TargetQQGroup,
    TargetQQPrivate,
    TargetQQGroupOpenId,
    TargetQQPrivateOpenId,
    TargetQQGuildChannel,
    TargetQQGuildDirect,
    TargetKaiheilaPrivate,
    TargetKaiheilaChannel,
    TargetOB12Unknow,
    TargetTelegramCommon,
    TargetTelegramForum,
    TargetFeishuPrivate,
    TargetFeishuGroup,
    TargetSatoriUnknown,
]


ConvertToArg = Callable[[PlatformTarget], Dict[str, Any]]
convert_to_arg_map: Dict[Tuple[SupportedPlatform, SupportedAdapters], ConvertToArg] = {}


def register_convert_to_arg(adapter: SupportedAdapters, platform: SupportedPlatform):
    def wrapper(func: ConvertToArg):
        convert_to_arg_map[(platform, adapter)] = func
        return func

    return wrapper


Extractor = Callable[[Event], PlatformTarget]
ExtractorWithBotSpecifier = Callable[[Event, Bot], PlatformTarget]
extractor_map: Dict[Type[Event], Union[Extractor, ExtractorWithBotSpecifier]] = {}


def register_target_extractor(event: Type[Event]):
    def wrapper(func: Union[Extractor, ExtractorWithBotSpecifier]):
        extractor_map[event] = func
        return func

    return wrapper


def extract_target(event: Event, bot: Optional[Bot] = None) -> PlatformTarget:
    "从事件中提取出发送目标，如果不能提取就抛出错误"
    for event_type in event.__class__.mro():
        if event_type in extractor_map:
            if not issubclass(event_type, Event):
                break
            if len(inspect.signature(extractor_map[event_type]).parameters.keys()) == 2:
                # extractor params: event, bot
                if bot is None:
                    raise RuntimeError(
                        f"event {event.__class__} need bot parameter to extract target",
                    )
                return extractor_map[event_type](event, bot)  # type: ignore
            else:
                return extractor_map[event_type](event)  # type: ignore
    raise RuntimeError(f"event {event.__class__} not supported")


def get_target(event: Event, bot: Optional[Bot] = None) -> Optional[PlatformTarget]:
    "从事件中提取出发送目标，如果不能提取就返回 None"
    try:
        return extract_target(event, bot)
    except RuntimeError:
        pass


Sender = Callable[
    [Bot, "MessageFactory", "PlatformTarget", Optional[Event], bool, bool],
    Awaitable["Receipt"],
]

sender_map: Dict[SupportedAdapters, Sender] = {}


def register_sender(adapter: SupportedAdapters):
    def wrapper(sender: Sender):
        sender_map[adapter] = sender
        return sender

    return wrapper


SaaTarget = Annotated[PlatformTarget, Depends(get_target)]

QQGuild_DMS = Callable[[TargetQQGuildDirect, Bot], Awaitable[int]]
qqguild_dms_map: Dict[SupportedAdapters, QQGuild_DMS] = {}


def register_qqguild_dms(adapter: SupportedAdapters):
    def wrapper(func: QQGuild_DMS):
        qqguild_dms_map[adapter] = func
        return func

    return wrapper


class QQGuildDMSManager:
    _cache: ClassVar[Dict[TargetQQGuildDirect, int]] = {}

    @classmethod
    def get_guild_id(cls, target: TargetQQGuildDirect) -> int:
        """从缓存中获取私聊所需 guild_id"""
        return cls._cache[target]

    @classmethod
    async def aget_guild_id(cls, target: TargetQQGuildDirect, bot: Bot) -> int:
        """获取私聊所需 guild_id"""
        if target in cls._cache:
            return cls._cache[target]

        adapter = extract_adapter_type(bot)
        if not (qqguild_dms := qqguild_dms_map.get(adapter)):
            raise RuntimeError(
                f"qqguild dms method for {adapter} not registered",
            )  # pragma: no cover
        guild_id = await qqguild_dms(target, bot)  # type: ignore
        cls._cache[target] = guild_id
        return guild_id
