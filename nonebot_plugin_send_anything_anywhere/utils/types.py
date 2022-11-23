import asyncio
from inspect import signature
from typing_extensions import Self
from typing import Callable, Awaitable, cast

from nonebot.internal.adapter.bot import Bot
from nonebot.internal.adapter.message import Message, MessageSegment

from .const import SupportedAdapters, supported_adapter_names


class AdapterNotInstalled(Exception):
    def __init__(self, adapter_name: str) -> None:
        message = f'adapter "{adapter_name}" not installed, please install first'
        super().__init__(self, message)


class AdapterNotSupported(Exception):
    def __init__(self, adapter_name: str) -> None:
        message = f'adapter "{adapter_name}" not supported'
        super().__init__(self, message)


class MessageSegmentFactory:
    _converters: dict[
        SupportedAdapters,
        Callable[[Self], MessageSegment | Awaitable[MessageSegment]]
        | Callable[[Self, Bot], MessageSegment | Awaitable[MessageSegment]],
    ] = {}

    async def convert(self, bot: Bot) -> MessageSegment:
        adapter_name = bot.adapter.get_name()
        if adapter_name not in supported_adapter_names:
            raise AdapterNotSupported(adapter_name)
        if converter := self._converters[adapter_name]:
            if len(signature(converter).parameters) == 1:
                converter = cast(
                    Callable[[Self], MessageSegment | Awaitable[MessageSegment]],
                    converter,
                )
                res = converter(self)
            elif len(signature(converter).parameters) == 2:
                converter = cast(
                    Callable[[Self, Bot], MessageSegment | Awaitable[MessageSegment]],
                    converter,
                )
                res = converter(self, bot)
            else:
                raise RuntimeError()
            if asyncio.iscoroutine(res):
                return await res
            else:
                res = cast(MessageSegment, res)
                return res
        raise AdapterNotInstalled(adapter_name)
