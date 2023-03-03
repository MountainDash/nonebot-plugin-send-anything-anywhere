from functools import partial
from typing import Literal, Optional

from ..types import Text, Image, Reply, Mention
from ..utils import (
    MessageFactory,
    SupportedAdapters,
    AbstractSendTarget,
    register_ms_adapter,
)


class SendTargetOneBot11(AbstractSendTarget):
    adapter_type: Literal[SupportedAdapters.onebot_v11] = SupportedAdapters.onebot_v11
    group_id: Optional[int] = None
    user_id: Optional[int] = None
    message_type: Optional[Literal["private", "group"]] = None


try:
    from nonebot.adapters.onebot.v11.message import Message, MessageSegment

    adapter = SupportedAdapters.onebot_v11
    register_onebot_v11 = partial(register_ms_adapter, adapter)

    MessageFactory.register_adapter_message(SupportedAdapters.onebot_v11, Message)

    @register_onebot_v11(Text)
    def _text(t: Text) -> MessageSegment:
        return MessageSegment.text(t.data["text"])

    @register_onebot_v11(Image)
    async def _image(i: Image) -> MessageSegment:
        return MessageSegment.image(i.data["image"])

    @register_onebot_v11(Mention)
    async def _mention(m: Mention) -> MessageSegment:
        return MessageSegment.at(m.data["user_id"])

    @register_onebot_v11(Reply)
    async def _reply(r: Reply) -> MessageSegment:
        return MessageSegment.reply(int(r.data["message_id"]))

except ImportError:
    pass
except Exception as e:
    raise e
