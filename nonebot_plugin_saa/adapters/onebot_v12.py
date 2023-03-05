from io import BytesIO
from pathlib import Path
from functools import partial
from typing import Literal, Optional

from nonebot.adapters import Event
from nonebot.adapters import Bot as BaseBot
from nonebot.adapters.onebot.v12 import Message, MessageEvent

from nonebot_plugin_saa.utils.registry import register_target_extractor

from ..types import Text, Image, Reply, Mention
from ..utils import (
    MessageFactory,
    SupportedAdapters,
    AbstractSendTarget,
    MessageSegmentFactory,
    register_sender,
    extract_send_target,
    register_ms_adapter,
    assamble_message_factory,
)


class SendTargetOneBot12(AbstractSendTarget):
    adapter_type: Literal[SupportedAdapters.onebot_v12] = SupportedAdapters.onebot_v12
    detail_type: Literal["private", "group", "channel"]
    user_id: Optional[str] = None
    group_id: Optional[str] = None
    guild_id: Optional[str] = None
    channel_id: Optional[str] = None


try:
    from nonebot.adapters.onebot.v12 import (
        Bot,
        MessageSegment,
        GroupMessageEvent,
        ChannelMessageEvent,
        PrivateMessageEvent,
    )

    adapter = SupportedAdapters.onebot_v12
    register_onebot_v12 = partial(register_ms_adapter, adapter)

    MessageFactory.register_adapter_message(adapter, Message)

    @register_onebot_v12(Text)
    def _text(t: Text) -> MessageSegment:
        return MessageSegment.text(t.data["text"])

    @register_onebot_v12(Image)
    async def _image(i: Image, bot: BaseBot) -> MessageSegment:
        if not isinstance(bot, Bot):
            raise TypeError(f"Unsupported type of bot: {type(bot)}")
        image = i.data["image"]
        name = i.data["name"]
        if isinstance(image, str):
            resp = await bot.upload_file(type="url", name=name, url=image)
        elif isinstance(image, Path):
            resp = await bot.upload_file(
                type="path", name=name, path=str(image.resolve())
            )
        elif isinstance(image, BytesIO):
            image = image.getvalue()
            resp = await bot.upload_file(type="data", name=name, data=image)
        elif isinstance(image, bytes):
            resp = await bot.upload_file(type="data", name=name, data=image)
        else:
            raise TypeError(f"Unsupported type of image: {type(image)}")

        file_id = resp["file_id"]
        return MessageSegment.image(file_id)

    @register_onebot_v12(Mention)
    async def _mention(m: Mention) -> MessageSegment:
        return MessageSegment.mention(m.data["user_id"])

    @register_onebot_v12(Reply)
    async def _reply(r: Reply) -> MessageSegment:
        return MessageSegment.reply(r.data["message_id"])

    @register_target_extractor(PrivateMessageEvent)
    def _extract_private_msg_event(event: Event) -> SendTargetOneBot12:
        assert isinstance(event, PrivateMessageEvent)
        return SendTargetOneBot12(detail_type="private", user_id=event.user_id)

    @register_target_extractor(GroupMessageEvent)
    def _extract_group_msg_event(event: Event) -> SendTargetOneBot12:
        assert isinstance(event, GroupMessageEvent)
        return SendTargetOneBot12(detail_type="group", group_id=event.group_id)

    @register_target_extractor(ChannelMessageEvent)
    def _extarct_channel_msg_event(event: Event) -> SendTargetOneBot12:
        assert isinstance(event, ChannelMessageEvent)
        return SendTargetOneBot12(
            detail_type="channel", channel_id=event.channel_id, guild_id=event.guild_id
        )

    @register_sender(SupportedAdapters.onebot_v12)
    async def send(
        bot,
        msg: MessageFactory[MessageSegmentFactory],
        target,
        event,
        at_sender: bool,
        reply: bool,
    ):
        assert isinstance(bot, Bot)
        assert isinstance(target, SendTargetOneBot12)

        send_target = extract_send_target(event)

        if event:
            assert isinstance(event, MessageEvent)
            full_msg = assamble_message_factory(
                msg, Mention(event.user_id), Reply(event.message_id), at_sender, reply
            )
        else:
            full_msg = msg
        msg_to_send = await full_msg.build(bot)
        assert isinstance(msg_to_send, Message)
        await bot.send_message(message=msg_to_send, **send_target.arg_dict())

except ImportError:
    pass
except Exception as e:
    raise e
