from io import BytesIO
from pathlib import Path
from functools import partial
from typing import Any, Dict, Union

from nonebot.adapters import Event
from nonebot.adapters import Bot as BaseBot

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
    register_target_extractor,
)

try:
    import aiohttp
    from nonebot.adapters.discord import Bot
    from nonebot.adapters.discord.message import Message, MessageSegment
    from nonebot.adapters.discord.event import (
        MessageEvent,
        MessageCreateEvent,
        ChannelPinsUpdateEvent,
    )

    adapter = SupportedAdapters.discord
    register_discord = partial(register_ms_adapter, adapter)

    MessageFactory.register_adapter_message(SupportedAdapters.discord, Message)

    @register_discord(Text)
    def _text(t: Text) -> MessageSegment:
        return MessageSegment.text(t.data["text"])

    @register_discord(Image)
    async def _image(i: Image, bot: BaseBot) -> MessageSegment:
        if not isinstance(bot, Bot):
            raise TypeError(f"Unsupported type of bot: {type(bot)}")
        image = i.data["image"]
        img_bytes = b""
        if isinstance(image, Union[str, Path]):
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
        sent_msg = await bot.send_to(message=message_to_send, **target.arg_dict(bot))
        if sent_msg:
            sent_data = sent_msg.dict()
            sent_data["msg_id"] = str(sent_msg.id)
            return sent_data
        else:
            return None

except ImportError:
    pass
except Exception as e:
    raise e
