from functools import partial
from io import BytesIO
from pathlib import Path
from typing import Any, Dict

from nonebot.adapters import Bot as BaseBot
from nonebot.adapters import Event

from ..types import Text, Image, Reply, Mention
from ..utils import (
    MessageFactory,
    PlatformTarget,
    SupportedAdapters,
    SupportedPlatform,
    TargetDiscordChannel,
    MessageSegmentFactory,
    register_sender,
    register_ms_adapter,
    register_convert_to_arg,
    assamble_message_factory,
    register_target_extractor, register_editor, SupportedEditorAdapters,
)

try:
    import aiohttp
    from nonebot.adapters.discord import Bot
    from nonebot.adapters.discord.bot import parse_message
    from nonebot.adapters.discord.message import Message, MessageSegment
    from nonebot.adapters.discord.event import (
        MessageEvent,
        MessageCreateEvent,
        ChannelPinsUpdateEvent,
    )

    adapter = SupportedAdapters.discord
    register_discord = partial(register_ms_adapter, adapter)

    MessageFactory.register_adapter_message(SupportedAdapters.discord, Message)


    async def process_message(bot: Bot, msg, at_sender, reply, event=None):
        if event:
            assert isinstance(event, MessageEvent)
            full_msg = assamble_message_factory(
                msg,
                Mention(event.get_user_id()),
                Reply(event.message_id),
                at_sender,
                reply,
            )
        else:
            full_msg = msg
        message_to_send = Message()
        for message_segment_factory in full_msg:
            message_segment = await message_segment_factory.build(bot)
            message_to_send += message_segment
        return message_to_send


    @register_discord(Text)
    def _text(t: Text) -> MessageSegment:
        return MessageSegment.text(t.data["text"])


    @register_discord(Image)
    async def _image(i: Image, bot: BaseBot) -> MessageSegment:
        if not isinstance(bot, Bot):
            raise TypeError(f"Unsupported type of bot: {type(bot)}")
        image = i.data["image"]
        img_bytes = b""
        if isinstance(image, (str, Path)):
            path = Path(image)
            if i.data["name"] == "image":
                if path.suffix not in [".jpg", ".jpeg", ".png", ".gif"]:
                    i.data["name"] = path.with_suffix(".png").name
                else:
                    i.data["name"] = path.name
            if path.exists():
                try:
                    with path.open("rb") as f:
                        img_bytes = f.read()
                except Exception as error:
                    raise Exception(f"Error reading local image: {str(error)}")
            else:
                async with aiohttp.ClientSession() as session:
                    async with session.get(str(image)) as response:
                        if response.status == 200:
                            img_bytes = await response.read()
                        else:
                            raise Exception(
                                f"Error downloading image, status code: {response.status}"  # noqa: E501
                            )
        elif isinstance(image, bytes):
            img_bytes = image
        elif isinstance(image, BytesIO):
            img_bytes = image.read()
        else:
            raise TypeError("Invalid image type")

        return MessageSegment.attachment(
            content=img_bytes,
            file=i.data["name"] if i.data["name"] != "image" else "image.png",
        )


    @register_discord(Mention)
    async def _mention(m: Mention) -> MessageSegment:
        return MessageSegment.mention_user(user_id=int(m.data["user_id"]))


    @register_discord(Reply)
    async def _reply(r: Reply) -> MessageSegment:
        return MessageSegment.reference(reference=int(r.data["message_id"]))


    @register_target_extractor(ChannelPinsUpdateEvent)
    @register_target_extractor(MessageCreateEvent)
    @register_target_extractor(MessageEvent)
    def _extract_msg_event(event: Event) -> TargetDiscordChannel:
        assert isinstance(event, MessageEvent)
        return TargetDiscordChannel(channel_id=event.channel_id)


    @register_convert_to_arg(adapter, SupportedPlatform.discord_channel)
    def _gen_channel(target: PlatformTarget) -> Dict[str, Any]:
        assert isinstance(target, TargetDiscordChannel)
        return {
            "channel_id": target.channel_id,
        }


    @register_sender(SupportedAdapters.discord)
    async def send(
        bot: Bot,
        msg: MessageFactory[MessageSegmentFactory],
        target,
        event,
        at_sender: bool,
        reply: bool,
    ):
        assert isinstance(bot, Bot)
        assert isinstance(target, TargetDiscordChannel)
        message_to_send = await process_message(bot, msg, at_sender, reply, event)
        sent_msg = await bot.send_to(message=message_to_send, **target.arg_dict(bot))
        if sent_msg:
            sent_data = sent_msg.dict()
            sent_data["msg_id"] = str(sent_msg.id)
            return sent_data
        else:
            return None


    @register_editor(SupportedEditorAdapters.discord)
    async def edit(
        bot: Bot,
        msg: MessageFactory[MessageSegmentFactory],
        target,
        message_target,
        event,
        at_sender: bool,
        reply: bool,
    ):
        message_to_send = await process_message(bot, msg, at_sender, reply, event)
        message_data = parse_message(message_to_send)
        del message_data["sticker_ids"]
        del message_data["message_reference"]
        await bot.edit_message(channel_id=target.channel_id, message_id=message_target.message_id, **message_data)

except ImportError:
    pass
except Exception as e:
    raise e
