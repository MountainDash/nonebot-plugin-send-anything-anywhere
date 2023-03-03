from functools import partial
from typing import Literal, Optional

from ..types import Text, Image, Mention
from ..utils import SupportedAdapters, AbstractSendTarget, register_ms_adapter


class SendTargetQQGuild(AbstractSendTarget):
    adapter_type: Literal[SupportedAdapters.qqguild] = SupportedAdapters.qqguild
    message_type: Literal["private", "channel"]
    recipient_id: Optional[str] = None
    source_guild_id: Optional[str] = None
    guild_id: Optional[str] = None
    channel_id: Optional[str] = None


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
