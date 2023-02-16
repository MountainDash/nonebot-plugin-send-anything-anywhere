from functools import partial

from ..types import Text
from ..utils import MessageFactory, SupportedAdapters, register_ms_adapter

try:
    from nonebot.adapters.onebot.v11.message import Message, MessageSegment

    adapter = SupportedAdapters.onebot_v11
    register_nonebot_v11 = partial(register_ms_adapter, adapter)

    MessageFactory.register_adapter_message(SupportedAdapters.onebot_v11, Message)

    @register_nonebot_v11(Text)
    def _text(t: Text) -> MessageSegment:
        return MessageSegment.text(t.data["text"])

except ImportError:
    pass
except Exception as e:
    raise e
