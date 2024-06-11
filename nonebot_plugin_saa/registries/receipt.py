from typing import Any
from abc import abstractmethod

from nonebot import get_bot
from nonebot.adapters import Bot

from .message_id import MessageId
from .meta import SerializationMeta
from ..utils import SupportedAdapters


class Receipt(SerializationMeta):
    _index_key = "adapter_name"

    adapter_name: SupportedAdapters
    bot_id: str

    def _get_bot(self) -> Bot:
        return get_bot(self.bot_id)

    async def revoke(self): ...

    @property
    def raw(self) -> Any: ...

    @abstractmethod
    def extract_message_id(self) -> MessageId:
        """从 Receipt 中提取 MessageId"""
        raise NotImplementedError
