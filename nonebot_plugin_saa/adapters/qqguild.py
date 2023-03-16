from functools import partial

from nonebot.adapters import Event

from ..types import Text, Image, Reply, Mention
from ..utils import (
    MessageFactory,
    PlatformTarget,
    SupportedAdapters,
    TargetQQGuildDirect,
    TargetQQGuildChannel,
    MessageSegmentFactory,
    register_sender,
    register_ms_adapter,
    assamble_message_factory,
    register_target_extractor,
)

try:
    from nonebot.adapters.qqguild import (
        Bot,
        Message,
        MessageEvent,
        MessageSegment,
        DirectMessageCreateEvent,
    )

    adapter = SupportedAdapters.qqguild
    register_qqguild = partial(register_ms_adapter, adapter)

    MessageFactory.register_adapter_message(adapter, Message)

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

    @register_qqguild(Reply)
    def _reply(r: Reply) -> MessageSegment:
        return MessageSegment.reference(r.data["message_id"])

    @register_target_extractor(MessageEvent)
    def extract_message_event(event: Event) -> PlatformTarget:
        assert isinstance(event, MessageEvent)
        if not event.to_me:
            assert event.channel_id
            return TargetQQGuildChannel(channel_id=int(event.channel_id))
        else:
            # TODO send dms not support yet
            assert event.guild_id
            assert event.author and event.author.id
            return TargetQQGuildDirect(
                source_guild_id=event.guild_id, recipient_id=event.author.id
            )

    @register_sender(SupportedAdapters.qqguild)
    async def send(
        bot,
        msg: MessageFactory[MessageSegmentFactory],
        target,
        event,
        at_sender: bool,
        reply: bool,
    ):
        assert isinstance(bot, Bot)
        assert isinstance(target, TargetQQGuildChannel | TargetQQGuildDirect)

        full_msg = msg
        if event:
            assert isinstance(event, MessageEvent)
            assert event.author
            assert event.id
            full_msg = assamble_message_factory(
                msg, Mention(str(event.author.id)), Reply(event.id), at_sender, reply
            )

        # parse Message
        message = await full_msg._build(bot)
        assert isinstance(message, Message)
        content = message.extract_content()

        if embed := (message["embed"] or None):
            embed = embed[-1].data["embed"]
        if ark := (message["ark"] or None):
            ark = ark[-1].data["ark"]
        if image := (message["attachment"] or None):
            image = image[-1].data["url"]
        if file_image := (message["file_image"] or None):
            file_image = file_image[-1].data["content"]
        if markdown := (message["markdown"] or None):
            markdown = markdown[-1].data["markdown"]
        if reference := (message["reference"] or None):
            reference = reference[-1].data["reference"]

        if event:  # reply to user
            if isinstance(event, DirectMessageCreateEvent):
                await bot.post_dms_messages(
                    guild_id=event.guild_id,
                    msg_id=event.id,
                    content=content,
                    embed=embed,
                    ark=ark,  # type: ignore
                    image=image,  # type: ignore
                    file_image=file_image,  # type: ignore
                    markdown=markdown,  # type: ignore
                    message_reference=reference,  # type: ignore
                )
            else:
                await bot.post_messages(
                    channel_id=event.channel_id,
                    msg_id=event.id,
                    content=content,
                    embed=embed,  # type: ignore
                    ark=ark,  # type: ignore
                    image=image,  # type: ignore
                    file_image=file_image,  # type: ignore
                    markdown=markdown,  # type: ignore
                    message_reference=reference,  # type: ignore
                )
        else:
            if isinstance(target, TargetQQGuildChannel):
                assert target.channel_id
                await bot.post_messages(
                    channel_id=target.channel_id,
                    content=content,
                    embed=embed,
                    ark=ark,
                    image=image,
                    file_image=file_image,
                    markdown=markdown,
                    message_reference=reference,
                )
            else:
                raise NotImplementedError("QQ频道主动发送私信暂未实现")

except ImportError:
    pass
except Exception as e:
    raise e
