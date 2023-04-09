from typing import Dict, Union

from nonebot.adapters import Bot, MessageSegment

from ..utils import (
    CustomBuildFunc,
    SupportedAdapters,
    AdapterNotSupported,
    MessageSegmentFactory,
    do_build_custom,
    extract_adapter_type,
)


class Custom(MessageSegmentFactory):
    "用户自定义的 MessageSegment"

    def __init__(
        self,
        ms_dict: Dict[SupportedAdapters, Union[MessageSegment, CustomBuildFunc]],
    ):
        """
        自定义 MessageSegment

        参数:
            ms_dict: 字典，key 为 SupportedAdapters，
                     val 为 MessageSegment 或 Bot -> MessageSegment 的函数，
                     规定为各个适配器返回的 MessageSegment
        """
        super().__init__()
        for k, v in ms_dict.items():
            self._register_custom_builder(k, v)

    async def build(self, bot: Bot) -> MessageSegment:
        adapter_name = extract_adapter_type(bot)
        if not (ms_builder := self._custom_builders.get(adapter_name)):
            raise AdapterNotSupported(adapter_name)

        ms = await do_build_custom(ms_builder, bot)
        return ms
