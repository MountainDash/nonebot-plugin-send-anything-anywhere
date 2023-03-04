from functools import partial
from typing import Literal, Optional

from nonebot.adapters import Event

from ..types import Text, Image, Mention
from ..utils import (
    SupportedAdapters,
    AbstractSendTarget,
    register_ms_adapter,
    register_target_extractor,
)


class SendTargetQQGuild(AbstractSendTarget):
    adapter_type: Literal[SupportedAdapters.qqguild] = SupportedAdapters.qqguild
    message_type: Literal["private", "channel"]
    recipient_id: Optional[str] = None
    source_guild_id: Optional[str] = None
    guild_id: Optional[int] = None
    channel_id: Optional[int] = None


try:
    from nonebot.adapters.qqguild import MessageEvent, MessageSegment

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

    @register_target_extractor(MessageEvent)
    def extract_message_event(event: Event) -> SendTargetQQGuild:
        assert isinstance(event, MessageEvent)
        if not event.to_me:
            return SendTargetQQGuild(
                message_type="channel",
                channel_id=event.channel_id,
                guild_id=event.guild_id,
            )
        else:
            # TODO send dms not support yet
            return SendTargetQQGuild(
                message_type="private",
                channel_id=event.channel_id,
                guild_id=event.guild_id,
            )

except ImportError:
    pass
except Exception as e:
    raise e
