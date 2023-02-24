from functools import partial

from ..types import Text, Image, Mention
from ..utils import SupportedAdapters, register_ms_adapter

try:
    from nonebot.adapters.qqguild import MessageSegment

    adapter = SupportedAdapters.qqguild
    register_qqguild = partial(register_ms_adapter, adapter)

    @register_qqguild(Text)
    def _text(t: Text) -> MessageSegment:
        return MessageSegment.text(t.data["text"])

    @register_qqguild(Image)
    def _image(i: Image) -> MessageSegment:
        if isinstance(i.data["image"], str):
            return MessageSegment.image(i.data["image"])
        else:
            return MessageSegment.file_image(i.data["image"])

    @register_qqguild(Mention)
    def _mention(m: Mention) -> MessageSegment:
        return MessageSegment.mention_user(int(m.data["user_id"]))

except ImportError:
    pass
except Exception as e:
    raise e
