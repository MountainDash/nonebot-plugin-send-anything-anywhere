try:
    from nonebot_plugin_alconna.uniseg import Text, Other, Custom
    from nonebot_plugin_alconna.uniseg import UniMessage as UniMsg
    from nonebot_plugin_alconna.uniseg import Segment as AlcSegment
    from nonebot_plugin_alconna.uniseg.adapters import (
        EXPORTER_MAPPING as ALC_EXPORTER_MAPPING,
    )
except ImportError as e:
    raise ImportError(
        "请使用 `pip install nonebot-plugin-send-anything-anywhere[alc]` 安装所需依赖"
    ) from e

from enum import Enum, auto
from typing import TypeVar, Iterable, TypedDict

from nonebot.adapters import Bot

from ..utils import SupportedAdapters, extract_adapter_type
from ..abstract_factories import MessageFactory, MessageSegmentFactory

AMS = TypeVar("AMS", bound=AlcSegment)


class Fallback(Enum):
    Forbid = auto()
    Permit = auto()
    Already = auto()


class UnisegExtException(Exception):
    ...


class AlcSegmentBuildError(UnisegExtException):
    @classmethod
    def from_seg(cls, seg: AlcSegment, msg: str):
        return cls(f"Alc Segment [{seg.__class__}]>>|{seg}|<<: {msg}")


class UniSegmentUnsupport(UnisegExtException):
    ...


class UniMsgData(TypedDict):
    uniseg: AlcSegment
    fallback: Fallback


# alc_builder 借鉴自nonebot_plugin_alconna.uniseg.exporter.MessageExporter.export
async def _alc_builder(seg: AlcSegment, bot: Bot):
    adapter_name = extract_adapter_type(bot)
    seg_type = seg.__class__

    if isinstance(seg, Other):
        return seg.origin

    if not (exportor := ALC_EXPORTER_MAPPING.get(adapter_name)):
        raise AlcSegmentBuildError.from_seg(seg, f"在 {adapter_name} 上找不到对应的 Exportor")

    if seg_type in exportor._mapping:
        export_result = await exportor._mapping[seg_type](seg, bot)
        if isinstance(export_result, list):
            raise AlcSegmentBuildError.from_seg(
                seg,
                f"在 {adapter_name} 中构建出多个 MessageSegment, SAA 尚未支持其转换",
            )

        return export_result

    elif isinstance(seg, Custom):
        msg_type = exportor.get_message_type()
        return seg.export(msg_type)

    else:
        raise AlcSegmentBuildError.from_seg(seg, "不支持构建")


async def alc_builder(data: UniMsgData, bot: Bot):
    fallback = data["fallback"]
    seg = data["uniseg"]
    try:
        res = await _alc_builder(seg, bot)
    except AlcSegmentBuildError as e:
        if fallback is Fallback.Permit:
            return await alc_builder(
                UniMsgData(uniseg=Text(str(seg)), fallback=Fallback.Already), bot
            )
        elif fallback is Fallback.Forbid:
            raise AlcSegmentBuildError.from_seg(seg, "不允许 fallback") from e
        else:
            raise AlcSegmentBuildError.from_seg(seg, "fallback 失败") from e
    else:
        return res


class AlcMessageSegmentFactory(MessageSegmentFactory):
    data: UniMsgData

    def __init__(self, uniseg: AlcSegment, fallback: bool = False) -> None:
        self.data = UniMsgData(
            uniseg=uniseg, fallback=Fallback.Permit if fallback else Fallback.Forbid
        )
        self._register_alc_builder()
        super().__init__()

    def _register_alc_builder(self):
        def maker(msf: "AlcMessageSegmentFactory", bot: Bot):
            return alc_builder(data=msf.data, bot=bot)

        for adapter_name in SupportedAdapters:
            self._builders[adapter_name] = maker

    @classmethod
    def from_unimsg(cls, msg: UniMsg, fallback: bool = False):
        return [cls(m, fallback) for m in msg]

    @classmethod
    def from_str(cls, msg: str, fallback: bool = False):
        return cls(Text(msg), fallback=fallback)


class UniMessageFactory(MessageFactory):
    def __init__(
        self,
        message: "str | MessageSegmentFactory | AlcSegment | Iterable[str | MessageSegmentFactory | AlcSegment] | None" = None,  # noqa: E
        fallback: bool = False,
    ):
        if isinstance(message, AlcSegment):
            amessage = AlcMessageSegmentFactory(message)
        elif isinstance(message, Iterable):

            def convert(m: "str | MessageSegmentFactory | AlcSegment"):
                if isinstance(m, AlcSegment):
                    return AlcMessageSegmentFactory(m, fallback=fallback)
                else:
                    return m

            amessage = [convert(m) for m in message]

        else:
            amessage = message

        super().__init__(amessage)

    @classmethod
    def from_unimsg(cls, msg: UniMsg, fallback: bool = False):
        return cls([AlcMessageSegmentFactory(m, fallback) for m in msg])
