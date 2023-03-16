from io import BytesIO
from pathlib import Path
from functools import partial

from nonebot.adapters import Event
from nonebot.adapters import Bot as BaseBot

from ..types import Text, Image, Reply, Mention
from ..utils import (
    TargetQQGroup,
    MessageFactory,
    PlatformTarget,
    TargetQQPrivate,
    TargetOB12Unknow,
    SupportedAdapters,
    SupportedPlatform,
    TargetQQGuildChannel,
    MessageSegmentFactory,
    register_sender,
    register_ms_adapter,
    register_convert_to_arg,
    assamble_message_factory,
    register_target_extractor,
)

try:
    from nonebot.adapters.onebot.v12 import (  # ChannelMessageEvent,
        Bot,
        Message,
        MessageEvent,
        MessageSegment,
        GroupMessageEvent,
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
    def _extract_private_msg_event(event: Event) -> PlatformTarget:
        assert isinstance(event, PrivateMessageEvent)
        if event.self.platform == "qq":
            return TargetQQPrivate(user_id=int(event.user_id))
        return TargetOB12Unknow(detail_type="private", user_id=event.user_id)

    @register_target_extractor(GroupMessageEvent)
    def _extract_group_msg_event(event: Event) -> PlatformTarget:
        assert isinstance(event, GroupMessageEvent)
        if event.self.platform == "qq":
            return TargetQQGroup(group_id=int(event.group_id))
        return TargetOB12Unknow(detail_type="group", group_id=event.group_id)

    # @register_target_extractor(ChannelMessageEvent)
    # def _extarct_channel_msg_event(event: Event) -> PlatformTarget:
    #     assert isinstance(event, ChannelMessageEvent)
    #     if event.self.platform == 'qqguild': # all4one
    #         return TargetQQGuildChannel(channel_id=int(event.channel_id))
    #     return TargetOB12Unknow(
    #         detail_type="channel", channel_id=event.channel_id,
    #       guild_id=event.guild_id
    #     )

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

    # @register_convert_to_arg(adapter, SupportedPlatform.qq_guild_channel)
    # def _to_qq_guild_channel(target: PlatformTarget):
    #     assert isinstance(target, TargetQQGuildChannel)
    #     return {
    #             "detail_type": "channel",
    #             "channel_id": target.channel_id,
    #             }

    # @register_convert_to_arg(adapter, SupportedPlatform.qq_guild_direct)
    # def _to_qq_guild_direct(target: PlatformTarget):
    #     assert isinstance(target, TargetQQGuildDirect)
    #     return {
    #             "detail_type": "private",
    #             "guild_id": target.source_guild_id,
    #             }

    @register_convert_to_arg(adapter, SupportedPlatform.unknown_ob12)
    def _to_unknow(target: PlatformTarget):
        assert isinstance(target, TargetOB12Unknow)
        return target.dict(exclude={"platform_type"})

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
        assert isinstance(
            target,
            TargetQQGroup | TargetQQPrivate | TargetQQGuildChannel | TargetOB12Unknow,
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
        await bot.send_message(message=msg_to_send, **target.arg_dict(bot))

except ImportError:
    pass
except Exception as e:
    raise e
