from functools import partial
from typing import List, Union, Literal, Optional

from nonebot.adapters import Event
from nonebot.adapters import Bot as BaseBot

from ..utils import SupportedAdapters
from ..types import Text, Image, Reply, Mention
from ..auto_select_bot import register_list_targets
from ..abstract_factories import (
    MessageFactory,
    MessageSegmentFactory,
    register_ms_adapter,
    assamble_message_factory,
)
from ..registries import (
    Receipt,
    MessageId,
    PlatformTarget,
    QQGuildDMSManager,
    TargetQQGroupOpen,
    TargetQQPrivateOpen,
    TargetQQGuildDirectOpen,
    TargetQQGuildChannelOpen,
    register_sender,
    register_qqguild_dms,
    register_target_extractor,
)

try:
    from nonebot.adapters.qq.event import GuildMessageEvent
    from nonebot.adapters.qq.models import Message as ApiMessage
    from nonebot.adapters.qq.models import (
        PostC2CFilesReturn,
        PostGroupFilesReturn,
        PostC2CMessagesReturn,
        PostGroupMessagesReturn,
    )
    from nonebot.adapters.qq import (
        Bot,
        Message,
        MessageSegment,
        MessageCreateEvent,
        AtMessageCreateEvent,
        C2CMessageCreateEvent,
        DirectMessageCreateEvent,
        GroupAtMessageCreateEvent,
    )

    adapter = SupportedAdapters.qq
    register_qq = partial(register_ms_adapter, adapter)

    MessageFactory.register_adapter_message(adapter, Message)

    class QQMessageId(MessageId):
        adapter_name: Literal[adapter] = adapter
        message_id: str

    @register_qq(Text)
    def _text(t: Text) -> MessageSegment:
        return MessageSegment.text(t.data["text"])

    @register_qq(Image)
    def _image(i: Image) -> MessageSegment:
        if isinstance(i.data["image"], str):
            return MessageSegment.image(i.data["image"])
        else:
            return MessageSegment.file_image(i.data["image"])

    @register_qq(Mention)
    def _mention(m: Mention) -> MessageSegment:
        return MessageSegment.mention_user(m.data["user_id"])

    @register_qq(Reply)
    def _reply(r: Reply) -> MessageSegment:
        assert isinstance(r.data, QQMessageId)
        return MessageSegment.reference(r.data.message_id)

    @register_target_extractor(GuildMessageEvent)
    def extract_message_event(event: Event, bot: BaseBot) -> PlatformTarget:
        if isinstance(event, DirectMessageCreateEvent):
            assert event.guild_id
            assert event.author and event.author.id
            return TargetQQGuildDirectOpen(
                bot_id=bot.self_id,
                source_guild_id=event.guild_id,
                recipient_id=event.author.id,
            )
        elif isinstance(event, (MessageCreateEvent, AtMessageCreateEvent)):
            assert event.channel_id
            return TargetQQGuildChannelOpen(
                bot_id=bot.self_id, channel_id=event.channel_id
            )
        elif isinstance(event, GroupAtMessageCreateEvent):
            assert event.group_openid
            return TargetQQGroupOpen(bot_id=bot.self_id, group_id=event.group_openid)
        elif isinstance(event, C2CMessageCreateEvent):
            assert event.author.id
            return TargetQQPrivateOpen(bot_id=bot.self_id, user_id=event.author.id)
        else:
            raise ValueError(f"{type(event)} not supported")

    @register_target_extractor(C2CMessageCreateEvent)
    def extract_c2c_message_event(event: Event, bot: BaseBot) -> PlatformTarget:
        assert isinstance(event, C2CMessageCreateEvent)
        return TargetQQPrivateOpen(bot_id=bot.self_id, user_id=event.author.id)

    @register_target_extractor(GroupAtMessageCreateEvent)
    def extract_group_at_message_event(event: Event, bot: BaseBot) -> PlatformTarget:
        assert isinstance(event, GroupAtMessageCreateEvent)
        return TargetQQGroupOpen(bot_id=bot.self_id, group_id=event.group_openid)

    @register_qqguild_dms(adapter)
    async def get_dms(target: TargetQQGuildDirectOpen, bot: BaseBot) -> int:
        assert isinstance(bot, Bot)

        dms = await bot.post_dms(
            recipient_id=str(target.recipient_id),
            source_guild_id=str(target.source_guild_id),
        )
        assert dms.guild_id
        return int(dms.guild_id)

    class QQReceipt(Receipt):
        msg_return: Union[
            ApiMessage,
            PostC2CMessagesReturn,
            PostGroupMessagesReturn,
            PostC2CFilesReturn,
            PostGroupFilesReturn,
        ]
        adapter_name: Literal[adapter] = adapter

        async def revoke(self, hidetip=False):
            if not isinstance(self.msg_return, ApiMessage):
                raise NotImplementedError("only guild message can be revoked")

            assert self.msg_return.channel_id
            assert self.msg_return.id
            return await self._get_bot().delete_message(
                channel_id=self.msg_return.channel_id,
                message_id=self.msg_return.id,
                hidetip=hidetip,
            )

        @property
        def raw(self):
            return self.msg_return

    @register_sender(SupportedAdapters.qq)
    async def send(
        bot,
        msg: MessageFactory[MessageSegmentFactory],
        target: PlatformTarget,
        event: Optional[Event],
        at_sender: bool,
        reply: bool,
    ) -> QQReceipt:
        assert isinstance(bot, Bot)
        assert isinstance(
            target,
            (
                TargetQQGuildChannelOpen,
                TargetQQGuildDirectOpen,
                TargetQQGroupOpen,
                TargetQQPrivateOpen,
            ),
        )

        full_msg = msg
        if event:
            assert isinstance(
                event,
                (GuildMessageEvent, C2CMessageCreateEvent, GroupAtMessageCreateEvent),
            )
            assert event.author
            assert event.id
            full_msg = assamble_message_factory(
                msg,
                Mention(event.author.id),
                Reply(QQMessageId(message_id=event.id)),
                at_sender,
                reply,
            )

        # parse Message
        message = await full_msg._build(bot)
        assert isinstance(message, Message)

        if event:  # reply to user
            msg_return = await bot.send(event, message)
        else:
            if isinstance(target, TargetQQGuildDirectOpen):
                guild_id = await QQGuildDMSManager.aget_guild_id(target, bot)
                msg_return = await bot.send_to_dms(
                    guild_id=str(guild_id),
                    message=message,
                )
            elif isinstance(target, TargetQQGuildChannelOpen):
                msg_return = await bot.send_to_channel(
                    channel_id=str(target.channel_id),
                    message=message,
                )
            elif isinstance(target, TargetQQPrivateOpen):
                msg_return = await bot.send_to_c2c(
                    openid=str(target.user_id),
                    message=message,
                )
            elif isinstance(target, TargetQQGroupOpen):
                msg_return = await bot.send_to_group(
                    group_openid=str(target.group_id),
                    message=message,
                )
            else:
                raise ValueError(f"{type(event)} not supported")

        return QQReceipt(bot_id=bot.self_id, msg_return=msg_return)

    @register_list_targets(SupportedAdapters.qq)
    async def list_targets(bot: BaseBot) -> List[PlatformTarget]:
        assert isinstance(bot, Bot)

        targets = []

        # TODO: 私聊

        guilds = await bot.guilds()
        for guild in guilds:
            channels = await bot.get_channels(guild_id=guild.id)
            for channel in channels:
                targets.append(
                    TargetQQGuildChannelOpen(
                        bot_id=bot.self_id,
                        channel_id=channel.id,
                    )
                )

        return targets

except ImportError:
    pass
except Exception as e:
    raise e
