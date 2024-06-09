from io import BytesIO
from pathlib import Path
from functools import partial
from contextlib import suppress
from typing import Any, Dict, List, Optional, cast

from nonebot.adapters import Event
from nonebot.drivers import Request
from nonebot.adapters import Bot as BaseBot
from nonebot.adapters.discord.api.model import (
    File,
    Embed,
    MessageFlag,
    AllowedMention,
    AttachmentSend,
    DirectComponent,
)

from ..auto_select_bot import register_list_targets
from ..utils import SupportedAdapters, SupportedPlatform
from ..types import Text, Image, Reply, Mention, MentionAll
from ..abstract_factories import (
    MessageFactory,
    register_ms_adapter,
    assamble_message_factory,
)
from ..registries import (
    Receipt,
    MessageId,
    PlatformTarget,
    TargetDiscordChannel,
    register_sender,
    register_convert_to_arg,
    register_target_extractor,
    register_message_id_getter,
)

with suppress(ImportError):
    from nonebot.adapters.discord import Bot as BotDiscord
    from nonebot.adapters.discord.message import Message, MessageSegment
    from nonebot.adapters.discord.api.model import Snowflake, MessageGet, SnowflakeType
    from nonebot.adapters.discord.event import (
        MessageEvent,
        MessageCreateEvent,
        ChannelPinsUpdateEvent,
    )

    adapter = SupportedAdapters.discord
    register_discord = partial(register_ms_adapter, adapter)

    MessageFactory.register_adapter_message(SupportedAdapters.discord, Message)

    class DiscordMessageId(MessageId):
        adapter_name: SupportedAdapters = adapter
        message_id: SnowflakeType
        channel_id: Optional[SnowflakeType] = None

    @register_message_id_getter(MessageEvent)
    def _get_msg_id(event: Event) -> DiscordMessageId:
        assert isinstance(event, MessageEvent)
        return DiscordMessageId(
            message_id=event.message_id, channel_id=event.channel_id
        )

    @register_discord(Text)
    def _text(t: Text) -> MessageSegment:
        return MessageSegment.text(t.data["text"])

    @register_discord(Image)
    async def _image(i: Image, bot: BaseBot) -> MessageSegment:
        if not isinstance(bot, BotDiscord):
            raise TypeError(f"Unsupported type of bot: {type(bot)}")
        image = i.data["image"]
        image_name = i.data["name"]

        if isinstance(image, Path) and image.is_file():
            if image_name == "image" and image.suffix not in [
                ".jpg",
                ".jpeg",
                ".png",
                ".gif",
            ]:
                image_name = image.with_suffix(".png").name
            else:
                image_name = image.name

            with image.open("rb") as f:
                img_bytes = f.read()

        elif isinstance(image, str):
            req = Request("GET", image, timeout=10)
            resp = await bot.adapter.request(req)
            if resp.status_code != 200:
                raise RuntimeError(
                    f"Error downloading image, status code: {resp.status_code}, url: {image}"  # noqa: E501
                )
            img_bytes = resp.content
            if not isinstance(img_bytes, bytes):
                raise TypeError(f"Expected bytes, got something else {type(img_bytes)}")

        elif isinstance(image, bytes):
            img_bytes = image

        elif isinstance(image, BytesIO):
            img_bytes = image.getvalue()

        else:
            raise TypeError(f"Invalid image type {type(image)}")

        return MessageSegment.attachment(
            content=img_bytes,
            file=image_name,
        )

    @register_discord(Reply)
    def _reply(r: Reply) -> MessageSegment:
        assert isinstance(mid := r.data["message_id"], DiscordMessageId)
        return MessageSegment.reference(reference=mid.message_id)

    @register_discord(Mention)
    def _mention(m: Mention) -> MessageSegment:
        return MessageSegment.mention_user(user_id=Snowflake(m.data["user_id"]))

    @register_discord(MentionAll)
    def _mention_all(m: MentionAll) -> MessageSegment:
        # TODO: 限定可以@的范围（channel等）
        return MessageSegment.mention_everyone()

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

    class DiscordReceipt(Receipt):
        adapter_name: SupportedAdapters = adapter
        message_get: MessageGet

        async def revoke(self, reason: Optional[str] = None):
            return await cast(BotDiscord, self._get_bot()).delete_message(
                channel_id=self.message_get.channel_id,
                message_id=self.message_get.id,
                reason=reason,
            )

        async def edit(
            self,
            content: Optional[str] = None,
            embeds: Optional[List[Embed]] = None,
            flags: Optional[MessageFlag] = None,
            allowed_mentions: Optional[AllowedMention] = None,
            components: Optional[List[DirectComponent]] = None,
            files: Optional[List[File]] = None,
            attachments: Optional[List[AttachmentSend]] = None,
        ) -> "DiscordReceipt":
            mg = await cast(BotDiscord, self._get_bot()).edit_message(
                channel_id=self.message_get.channel_id,
                message_id=self.message_get.id,
                content=content,
                embeds=embeds,
                flags=flags,
                allowed_mentions=allowed_mentions,
                components=components,
                files=files,
                attachments=attachments,
            )
            return self.__class__(message_get=mg, bot_id=self.bot_id)

        async def pin(self, reason: Optional[str] = None):
            return await cast(BotDiscord, self._get_bot()).pin_message(
                channel_id=self.message_get.channel_id,
                message_id=self.message_get.id,
                reason=reason,
            )

        async def unpin(self, reason: Optional[str] = None):
            return await cast(BotDiscord, self._get_bot()).unpin_message(
                channel_id=self.message_get.channel_id,
                message_id=self.message_get.id,
                reason=reason,
            )

        async def react(self, emoji: str):
            return await cast(BotDiscord, self._get_bot()).create_reaction(
                channel_id=self.message_get.channel_id,
                message_id=self.message_get.id,
                emoji=emoji,
            )

        @property
        def raw(self) -> MessageGet:
            return self.message_get

        def extract_message_id(self) -> DiscordMessageId:
            return DiscordMessageId(
                message_id=self.message_get.id, channel_id=self.message_get.channel_id
            )

    @register_sender(adapter)
    async def send(
        bot,
        msg: MessageFactory,
        target,
        event,
        at_sender: bool,
        reply: bool,
    ) -> DiscordReceipt:
        assert isinstance(bot, BotDiscord)
        assert isinstance(target, TargetDiscordChannel)
        if event:
            assert isinstance(event, MessageEvent)
            full_msg = assamble_message_factory(
                msg,
                Mention(event.get_user_id()),
                Reply(
                    DiscordMessageId(
                        message_id=event.message_id, channel_id=event.channel_id
                    )
                ),
                at_sender,
                reply,
            )
        else:
            full_msg = msg
        message_to_send = Message()
        for message_segment_factory in full_msg:
            message_segment = await message_segment_factory.build(bot)
            message_to_send += message_segment
        resp = await bot.send_to(message=message_to_send, **target.arg_dict(bot))
        return DiscordReceipt(message_get=resp, bot_id=bot.self_id)

    @register_list_targets(adapter)
    async def list_targets(bot: BaseBot) -> List[PlatformTarget]:
        assert isinstance(bot, BotDiscord)
        channel_ids: List[Snowflake] = []
        guild_list = await bot.get_current_user_guilds()
        for guild in guild_list:
            channels = await bot.get_guild_channels(guild_id=guild.id)
            for channel in channels:
                channel_ids.append(channel.id)

        return [TargetDiscordChannel(channel_id=channel.id) for channel in channels]
