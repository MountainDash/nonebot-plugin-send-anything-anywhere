from nonebot.plugin import PluginMetadata

from .types import Text as Text
from .types import Image as Image
from .types import Reply as Reply
from . import adapters as adapters
from .types import Custom as Custom
from .types import Mention as Mention
from .utils import get_target as get_target
from .utils import TargetQQGroup as TargetQQGroup
from .utils import MessageFactory as MessageFactory
from .utils import PlatformTarget as PlatformTarget
from .utils import MessageTarget as MessageTarget
from .utils import extract_target as extract_target
from .utils import TargetQQPrivate as TargetQQPrivate
from .utils import TargetOB12Unknow as TargetOB12Unknow
from .utils import SupportedAdapters as SupportedAdapters
from .utils import TargetFeishuGroup as TargetFeishuGroup
from .utils import TargetFeishuPrivate as TargetFeishuPrivate
from .utils import TargetQQGuildDirect as TargetQQGuildDirect
from .utils import TargetTelegramForum as TargetTelegramForum
from .utils import TargetQQGuildChannel as TargetQQGuildChannel
from .utils import TargetTelegramCommon as TargetTelegramCommon
from .utils import MessageSegmentFactory as MessageSegmentFactory
from .utils import TargetKaiheilaChannel as TargetKaiheilaChannel
from .utils import TargetKaiheilaPrivate as TargetKaiheilaPrivate
from .utils import enable_auto_select_bot as enable_auto_select_bot
from .utils import AggregatedMessageFactory as AggregatedMessageFactory
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
        "~qqguild",
        "~telegram",
        "~feishu",
    },
)
