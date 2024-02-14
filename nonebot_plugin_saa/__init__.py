from nonebot.plugin import PluginMetadata

from .types import Text as Text
from .types import Image as Image
from .types import Reply as Reply
from . import adapters as adapters
from .types import Custom as Custom
from .types import Mention as Mention
from .registries import SaaTarget as SaaTarget
from .registries import get_target as get_target
from .registries import TargetQQGroup as TargetQQGroup
from .registries import PlatformTarget as PlatformTarget
from .registries import extract_target as extract_target
from .utils import SupportedAdapters as SupportedAdapters
from .registries import TargetQQPrivate as TargetQQPrivate
from .registries import TargetOB12Unknow as TargetOB12Unknow
from .registries import TargetDoDoChannel as TargetDoDoChannel
from .registries import TargetDoDoPrivate as TargetDoDoPrivate
from .registries import TargetFeishuGroup as TargetFeishuGroup
from .abstract_factories import MessageFactory as MessageFactory
from .registries import TargetFeishuPrivate as TargetFeishuPrivate
from .registries import TargetQQGroupOpenId as TargetQQGroupOpenId
from .registries import TargetQQGuildDirect as TargetQQGuildDirect
from .registries import TargetTelegramForum as TargetTelegramForum
from .registries import TargetQQGuildChannel as TargetQQGuildChannel
from .registries import TargetTelegramCommon as TargetTelegramCommon
from .registries import TargetKaiheilaChannel as TargetKaiheilaChannel
from .registries import TargetKaiheilaPrivate as TargetKaiheilaPrivate
from .registries import TargetQQPrivateOpenId as TargetQQPrivateOpenId
from .auto_select_bot import enable_auto_select_bot as enable_auto_select_bot
from .abstract_factories import MessageSegmentFactory as MessageSegmentFactory
from .abstract_factories import AggregatedMessageFactory as AggregatedMessageFactory

__plugin_meta__ = PluginMetadata(
    name="峯驰物流",
    description=("一个帮助处理不同 adapter 消息的适配和发送的插件 "),
    usage="请开发者参考文档",
    type="library",
    homepage="https://send-anything-anywhere.felinae98.cn/",
    supported_adapters={
        "~onebot.v11",
        "~onebot.v12",
        "~kaiheila",
        "~telegram",
        "~feishu",
        "~red",
        "~qq",
    },
)
