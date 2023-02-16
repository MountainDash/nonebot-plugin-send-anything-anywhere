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
    _builders: dict[
        SupportedAdapters,
        Callable[[Self], MessageSegment | Awaitable[MessageSegment]]
        | Callable[[Self, Bot], MessageSegment | Awaitable[MessageSegment]],
    ] = {}

    async def build(self, bot: Bot) -> MessageSegment:
        adapter_name = bot.adapter.get_name()
        if adapter_name not in supported_adapter_names:
            raise AdapterNotSupported(adapter_name)
        if builder := self._builders[adapter_name]:
            if len(signature(builder).parameters) == 1:
                builder = cast(
                    Callable[[Self], MessageSegment | Awaitable[MessageSegment]],
                    builder,
                )
                res = builder(self)
            elif len(signature(builder).parameters) == 2:
                builder = cast(
                    Callable[[Self, Bot], MessageSegment | Awaitable[MessageSegment]],
                    builder,
                )
                res = builder(self, bot)
            else:
                raise RuntimeError()
            if asyncio.iscoroutine(res):
                return await res
            else:
                res = cast(MessageSegment, res)
                return res
        raise AdapterNotInstalled(adapter_name)
