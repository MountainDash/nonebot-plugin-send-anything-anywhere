from typing import Callable

from nonebot.adapters import Bot, MessageSegment

from ..utils import (
    SupportedAdapters,
    AdapterNotSupported,
    MessageSegmentFactory,
    extract_adapter_type,
)


class Custom(MessageSegmentFactory):
    "用户自定义的 MessageSegment"
    ms_dict: dict[SupportedAdapters, MessageSegment | Callable[[Bot], MessageSegment]]

    def __init__(
        self,
        ms_dict: dict[
            SupportedAdapters, MessageSegment | Callable[[Bot], MessageSegment]
        ],
    ):
        """
        自定义 MessageSegment

        参数:
            ms_dict: 字典，key 为 SupportedAdapters，
                     val 为 MessageSegment 或 Bot -> MessageSegment 的函数，
                     规定为各个适配器返回的 MessageSegment
        """
        self.ms_dict = ms_dict

    async def build(self, bot: Bot) -> MessageSegment:
        adapter_name = extract_adapter_type(bot)
        if adapter_name not in self.ms_dict.keys():
            raise AdapterNotSupported(adapter_name)

        ms = self.ms_dict[adapter_name]
        if not isinstance(ms, MessageSegment):
            ms = ms(bot)

        return ms
