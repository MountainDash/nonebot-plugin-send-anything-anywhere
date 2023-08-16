from functools import partial
from io import BytesIO
from pathlib import Path
from typing import List

from nonebot.adapters import Bot as BaseBot
from nonebot.adapters import Event

from ..types import Text, Image, Reply, Mention
from ..utils import (
    Receipt,
    TargetQQGroup,
    MessageFactory,
    PlatformTarget,
    TargetQQPrivate,
    TargetOB12Unknow,
    QQGuildDMSManager,
    SupportedAdapters,
    SupportedPlatform,
    TargetQQGuildDirect,
    TargetQQGuildChannel,
    MessageSegmentFactory,
    get_bot_id,
    register_sender,
    register_get_bot_id,
    register_ms_adapter,
    register_qqguild_dms,
    register_list_targets,
    register_convert_to_arg,
    assamble_message_factory,
    register_target_extractor,
)

try:
    from nonebot.adapters.onebot.v12.exception import UnsupportedAction
    from nonebot.adapters.onebot.v12 import (
        Bot,
        Message,
        MessageEvent,
        MessageSegment,
        GroupMessageEvent,
        ChannelCreateEvent,
        ChannelDeleteEvent,
        ChannelMessageEvent,
        FriendDecreaseEvent,
        FriendIncreaseEvent,
        PrivateMessageEvent,
        GroupMessageDeleteEvent,
        GroupMemberDecreaseEvent,
        GroupMemberIncreaseEvent,
        ChannelMessageDeleteEvent,
        PrivateMessageDeleteEvent,
        ChannelMemberDecreaseEvent,
        ChannelMemberIncreaseEvent,
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
    def _extract_private_msg_event(event: Event) -> PlatformTarget:
        assert isinstance(event, PrivateMessageEvent)
        if event.self.platform == "qq":
            return TargetQQPrivate(user_id=int(event.user_id))
        if event.self.platform == "qqguild":
            event_dict = event.dict()
            return TargetQQGuildDirect(
                recipient_id=int(event.user_id),
                source_guild_id=event_dict["qqguild"]["src_guild_id"],
            )
        return TargetOB12Unknow(
            platform=event.self.platform, detail_type="private", user_id=event.user_id
        )


    @register_target_extractor(GroupMessageEvent)
    def _extract_group_msg_event(event: Event) -> PlatformTarget:
        assert isinstance(event, GroupMessageEvent)
        if event.self.platform == "qq":
            return TargetQQGroup(group_id=int(event.group_id))
        return TargetOB12Unknow(
            platform=event.self.platform, detail_type="group", group_id=event.group_id
        )


    @register_target_extractor(ChannelMessageEvent)
    def _extarct_channel_msg_event(event: Event) -> PlatformTarget:
        assert isinstance(event, ChannelMessageEvent)
        if event.self.platform == "qqguild":  # all4one
            return TargetQQGuildChannel(channel_id=int(event.channel_id))
        return TargetOB12Unknow(
            platform=event.self.platform,
            detail_type="channel",
            channel_id=event.channel_id,
            guild_id=event.guild_id,
        )


    @register_target_extractor(FriendIncreaseEvent)
    @register_target_extractor(FriendDecreaseEvent)
    @register_target_extractor(PrivateMessageDeleteEvent)
    def _extract_private_notice_event(event: Event) -> PlatformTarget:
        assert isinstance(
            event, (FriendIncreaseEvent, FriendDecreaseEvent, PrivateMessageDeleteEvent)
        )
        if event.self.platform == "qq":
            return TargetQQPrivate(user_id=int(event.user_id))
        return TargetOB12Unknow(
            platform=event.self.platform, detail_type="private", user_id=event.user_id
        )


    @register_target_extractor(GroupMemberIncreaseEvent)
    @register_target_extractor(GroupMemberDecreaseEvent)
    @register_target_extractor(GroupMessageDeleteEvent)
    def _extract_group_notice_event(event: Event) -> PlatformTarget:
        assert isinstance(
            event,
            (
                GroupMemberIncreaseEvent,
                GroupMemberDecreaseEvent,
                GroupMessageDeleteEvent,
            ),
        )
        if event.self.platform == "qq":
            return TargetQQGroup(group_id=int(event.group_id))
        return TargetOB12Unknow(
            platform=event.self.platform, detail_type="group", group_id=event.group_id
        )


    @register_target_extractor(ChannelMemberIncreaseEvent)
    @register_target_extractor(ChannelMemberDecreaseEvent)
    @register_target_extractor(ChannelMessageDeleteEvent)
    @register_target_extractor(ChannelCreateEvent)
    @register_target_extractor(ChannelDeleteEvent)
    def _extarct_channel_notice_event(event: Event) -> PlatformTarget:
        assert isinstance(
            event,
            (
                ChannelMemberIncreaseEvent,
                ChannelMemberDecreaseEvent,
                ChannelMessageDeleteEvent,
                ChannelCreateEvent,
                ChannelDeleteEvent,
            ),
        )
        if event.self.platform == "qqguild":  # all4one
            return TargetQQGuildChannel(channel_id=int(event.channel_id))
        return TargetOB12Unknow(
            platform=event.self.platform,
            detail_type="channel",
            channel_id=event.channel_id,
            guild_id=event.guild_id,
        )


    @register_convert_to_arg(adapter, SupportedPlatform.qq_group)
    def _to_qq_group(target: PlatformTarget):
        assert isinstance(target, TargetQQGroup)
        return {
            "detail_type": "group",
            "group_id": str(target.group_id),
        }


    @register_convert_to_arg(adapter, SupportedPlatform.qq_private)
    def _to_qq_private(target: PlatformTarget):
        assert isinstance(target, TargetQQPrivate)
        return {
            "detail_type": "private",
            "user_id": str(target.user_id),
        }


    @register_convert_to_arg(adapter, SupportedPlatform.qq_guild_channel)
    def _to_qq_guild_channel(target: PlatformTarget):
        assert isinstance(target, TargetQQGuildChannel)
        return {
            "detail_type": "channel",
            "channel_id": str(target.channel_id),
        }


    @register_convert_to_arg(adapter, SupportedPlatform.qq_guild_direct)
    def _to_qq_guild_direct(target: PlatformTarget):
        assert isinstance(target, TargetQQGuildDirect)
        return {
            "detail_type": "private",
            "guild_id": str(QQGuildDMSManager.get_guild_id(target)),
        }


    @register_qqguild_dms(adapter)
    async def _qqguild_dms(target: TargetQQGuildDirect, bot: BaseBot) -> int:
        assert isinstance(bot, Bot)

        resp = await bot.create_dms(
            user_id=str(target.recipient_id), src_guild_id=str(target.source_guild_id)
        )
        return resp["guild_id"]


    @register_convert_to_arg(adapter, SupportedPlatform.unknown_ob12)
    def _to_unknow(target: PlatformTarget):
        assert isinstance(target, TargetOB12Unknow)
        return target.dict(exclude={"platform", "platform_type"})


    class OB12Receipt(Receipt):
        message_id: str
        adapter_name = adapter


        async def revoke(self):
            return await self._get_bot().delete_message(message_id=self.message_id)

        @property
        def raw(self):
            return self.message_id



    @register_sender(SupportedAdapters.onebot_v12)
    async def send(
        bot,
        msg: MessageFactory[MessageSegmentFactory],
        target,
        event,
        at_sender: bool,
        reply: bool,
    ) -> OB12Receipt:
        assert isinstance(bot, Bot)
        assert isinstance(
            target,
            (
                TargetQQGroup,
                TargetQQPrivate,
                TargetQQGuildChannel,
                TargetQQGuildDirect,
                TargetOB12Unknow,
            ),
        )

        if event:
            assert isinstance(event, MessageEvent)
            full_msg = assamble_message_factory(
                msg, Mention(event.user_id), Reply(event.message_id), at_sender, reply
            )
        else:
            full_msg = msg
        msg_to_send = await full_msg.build(bot)
        assert isinstance(msg_to_send, Message)
        if bot.platform == "qqguild":
            assert isinstance(target, (TargetQQGuildChannel, TargetQQGuildDirect))
            if isinstance(target, TargetQQGuildDirect):
                await QQGuildDMSManager.aget_guild_id(target, bot)
            params = {}
            if event:
                # 传递 event_id，用来支持频道的被动消息
                params["event_id"] = event.id
            resp = await bot.send_message(
                message=msg_to_send,
                **target.arg_dict(bot),
                **params,
            )
        else:
            resp = await bot.send_message(message=msg_to_send, **target.arg_dict(bot))
        message_id = resp["message_id"]
        return OB12Receipt(bot_id=get_bot_id(bot), message_id=message_id)


    @register_list_targets(SupportedAdapters.onebot_v12)
    async def list_targets(bot: BaseBot) -> List[PlatformTarget]:
        assert isinstance(bot, Bot)

        targets = []
        try:
            friends = await bot.get_friend_list()
            for friend in friends:
                platform = bot.platform
                if platform == "qq":
                    targets.append(TargetQQPrivate(user_id=int(friend["user_id"])))
                elif platform == "qqguild":
                    # FIXME: 怎么获取 src_guild_id 捏？
                    pass
                else:
                    targets.append(
                        TargetOB12Unknow(
                            platform=platform,
                            detail_type="private",
                            user_id=friend["user_id"],
                        )
                    )

        except UnsupportedAction:  # pragma: no cover
            pass

        try:
            groups = await bot.get_group_list()
            for group in groups:
                platform = bot.platform
                if platform == "qq":
                    targets.append(TargetQQGroup(group_id=int(group["group_id"])))
                else:
                    targets.append(
                        TargetOB12Unknow(
                            platform=platform,
                            detail_type="group",
                            group_id=group["group_id"],
                        )
                    )

        except UnsupportedAction:  # pragma: no cover
            pass

        try:
            guilds = await bot.get_guild_list()
            for guild in guilds:
                channels = await bot.get_channel_list(guild_id=guild["guild_id"])
                for channel in channels:
                    platform = bot.platform
                    if platform == "qqguild":
                        targets.append(
                            TargetQQGuildChannel(channel_id=int(channel["channel_id"]))
                        )
                    else:
                        targets.append(
                            TargetOB12Unknow(
                                platform=platform,
                                detail_type="channel",
                                channel_id=channel["channel_id"],
                                guild_id=guild["guild_id"],
                            )
                        )

        except UnsupportedAction:  # pragma: no cover
            pass

        return targets



    @register_get_bot_id(adapter)
    def _get_bot_id(bot: BaseBot):
        assert isinstance(bot, Bot)
        return f"{bot.platform}-{bot.self_id}"

except ImportError:
    pass
except Exception as e:
    raise e
