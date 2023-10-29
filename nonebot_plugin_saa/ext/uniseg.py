try:
    from nonebot_plugin_alconna.uniseg import Other, Segment
    from nonebot_plugin_alconna.uniseg import UniMessage as UniMsg
    from nonebot_plugin_alconna.uniseg.adapters import MAPPING as alc_exportor_map
except ImportError as e:
    raise ImportError(
        "请使用 `pip install nonebot-plugin-send-anything-anywhere[alc]` 安装所需依赖"
    ) from e

from typing_extensions import override
from typing import Union, TypeVar, Iterable

from nonebot.adapters import Bot, Message, MessageSegment

from ..utils import extract_adapter_type
from ..abstract_factories import MessageFactory, MessageSegmentFactory

UMS = TypeVar("UMS", bound=Segment)


class UniSegmentUnsupport(Exception):
    ...


class UniMessageSegmentFactory(MessageSegmentFactory):
    data: Segment

    def __init__(self, uniseg: Segment) -> None:
        self.data = uniseg

    async def build(self, bot: Bot) -> MessageSegment:
        adapter_name = extract_adapter_type(bot)
        seg_type = self.data.__class__
        export_res = None
        if exportor := alc_exportor_map.get(adapter_name):
            exportor.segment_class = exportor.get_message_type().get_segment_class()
            export_res = await exportor._mapping[seg_type](self.data, bot)

        if not export_res and isinstance(self.data, Other):
            export_res = self.data.origin

        if not export_res:
            raise UniSegmentUnsupport(self.data)

        return export_res


class UniMessageFactory(MessageFactory):
    def __init__(
        self, message: Union[Iterable[Union[str, UMS]], str, UMS, None] = None
    ):
        self.unimsg = UniMsg(message)
        self.extend(map(UniMessageSegmentFactory, self.unimsg))

    @override
    async def build(self, bot: Bot) -> Message:
        return await self.unimsg.export(bot)
