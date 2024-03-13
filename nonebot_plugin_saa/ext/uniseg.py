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

from functools import partial
from typing_extensions import override
from typing import Union, TypeVar, Iterable, TypedDict

from nonebot.adapters import Bot, Message, MessageSegment

from ..utils import SupportedAdapters, extract_adapter_type
from ..abstract_factories import MessageFactory, MessageSegmentFactory

AMS = TypeVar("AMS", bound=AlcSegment)


class UnisegExtException(Exception):
    ...


class AlcSegmentBuildError(UnisegExtException):
    @classmethod
    def from_seg(cls, seg: AlcSegment, msg: str):
        return cls(f"Alc Segment [{seg.__class__}] -> {seg} <-: {msg}")


class UniSegmentUnsupport(UnisegExtException):
    ...


class UniMsgData(TypedDict):
    uniseg: AlcSegment
    fallback: bool


async def alc_builder(data: UniMsgData, bot: Bot):
    """抄自nonebot_plugin_alconna.uniseg.exporter.MessageExporter.export"""
    seg = data["uniseg"]
    fallback = data["fallback"]
    adapter_name = extract_adapter_type(bot)
    seg_type = seg.__class__

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

    elif isinstance(seg, Other):
        return seg.origin

    elif fallback:
        if not isinstance(
            res := alc_builder(UniMsgData(uniseg=Text(str(seg)), fallback=False), bot),
            MessageSegment,
        ):
            raise AlcSegmentBuildError.from_seg(seg, "fallback 失败！")
        else:
            return res
    else:
        raise AlcSegmentBuildError.from_seg(seg, "不支持构建")


class AlcMessageSegmentFactory(MessageSegmentFactory):
    data: UniMsgData

    def __init__(self, uniseg: AlcSegment, fallback: bool = False) -> None:
        self.data = UniMsgData(uniseg=uniseg, fallback=fallback)
        self._init_alc_builder()
        super().__init__()

    def _init_alc_builder(self):
        def maker(msf: "AlcMessageSegmentFactory", bot: Bot):
            return alc_builder(data=msf.data, bot=bot)

        for adapter_name in SupportedAdapters:
            self._builders[adapter_name] = maker

    @classmethod
    def from_unimsg(cls, msg: UniMsg, fallback: bool = False):
        return [*map(partial(cls, fallback=fallback), msg)]

    @classmethod
    def from_str(cls, msg: str, fallback: bool = False):
        return cls(Text(msg), fallback=fallback)


class AlcMessageFactory(MessageFactory):
    def __init__(
        self,
        message: Union[Iterable[Union[str, AMS]], str, AMS, None] = None,
        fallback: bool = False,
    ):
        self.unimsg = UniMsg(message)
        self.extend(
            map(partial(AlcMessageSegmentFactory, fallback=fallback), self.unimsg)
        )
        super().__init__()

    @override
    async def build(self, bot: Bot) -> Message:
        return await self.unimsg.export(bot)


class UniMessageFactory(MessageFactory):
    def __init__(
        self,
        message: "str | MessageSegmentFactory | AlcSegment | Iterable[str | MessageSegmentFactory | AlcSegment] | None" = None,  # noqa: E
        fallback: bool = False,
    ):
        if isinstance(message, AlcSegment):
            amessage = AlcMessageSegmentFactory(message)
        elif isinstance(message, UniMsg):
            amessage = map(partial(AlcMessageSegmentFactory, fallback=fallback), message)  # type: ignore 已经在 UniMsg 内部全部转换为 uniseg 了  # noqa: E501
        elif isinstance(message, Iterable):

            def convert(m: "str | MessageSegmentFactory | AlcSegment"):
                if isinstance(m, AlcSegment):
                    return AlcMessageSegmentFactory(m, fallback=fallback)
                else:
                    return m

            amessage = map(convert, message)

        else:
            amessage = message

        super().__init__(amessage)

    @classmethod
    def from_unimsg(cls, msg: UniMsg, fallback: bool = False):
        return cls(map(partial(AlcMessageSegmentFactory, fallback=fallback), msg))
