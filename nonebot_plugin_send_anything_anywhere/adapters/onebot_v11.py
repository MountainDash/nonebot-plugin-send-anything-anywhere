from functools import partial

from ..types import Text, Image
from ..utils import MessageFactory, SupportedAdapters, register_ms_adapter

try:
    from nonebot.adapters.onebot.v11.message import Message, MessageSegment

    adapter = SupportedAdapters.onebot_v11
    register_nonebot_v11 = partial(register_ms_adapter, adapter)

    MessageFactory.register_adapter_message(SupportedAdapters.onebot_v11, Message)

    @register_nonebot_v11(Text)
    def _text(t: Text) -> MessageSegment:
        return MessageSegment.text(t.data["text"])

    @register_nonebot_v11(Image)
    async def _image(i: Image) -> MessageSegment:
        return MessageSegment.image(i.data["image"])

except ImportError:
    pass
except Exception as e:
    raise e
