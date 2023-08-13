from functools import partial
from typing import Any, Dict, List

from nonebot.adapters import Bot as BaseBot
from nonebot.adapters import Event

from ..types import Text, Image, Reply, Mention
from ..utils import (
    MessageFactory,
    PlatformTarget,
    SupportedAdapters,
    SupportedPlatform,
    MessageSegmentFactory,
    register_sender,
    register_ms_adapter,
    register_list_targets,
    register_convert_to_arg,
    assamble_message_factory,
    register_target_extractor,
)
from ..utils.platform_send_target import TargetKaiheilaChannel, TargetKaiheilaPrivate

try:
    from nonebot.adapters.kaiheila import Bot
    from nonebot.adapters.kaiheila.api import Guild, Channel, UserChat
    from nonebot.adapters.kaiheila.message import Message, MessageSegment
    from nonebot.adapters.kaiheila.event import (
        MessageEvent,
        ChannelMessageEvent,
        PrivateMessageEvent,
    )

    def _unwrap_paging_api(field: str):
        def decorator(func):
            async def wrapper(*args, **kwargs):
                result = await func(*args, **kwargs)
                while True:
                    for x in getattr(result, field):
                        yield x

                    if result.meta.page != result.meta.page_total:
                        result = await func(*args, **kwargs, page=result.meta.page + 1)
                    else:
                        break

            return wrapper

        return decorator

    adapter = SupportedAdapters.kaiheila
    register_kaiheila = partial(register_ms_adapter, adapter)

    MessageFactory.register_adapter_message(SupportedAdapters.kaiheila, Message)

    @register_kaiheila(Text)
    def _text(t: Text) -> MessageSegment:
        return MessageSegment.text(t.data["text"])

    @register_kaiheila(Image)
    async def _image(i: Image, bot: BaseBot) -> MessageSegment:
        if not isinstance(bot, Bot):
            raise TypeError(f"Unsupported type of bot: {type(bot)}")

        file_key = await bot.upload_file(i.data["image"], i.data["name"])
        return MessageSegment.image(file_key)

    @register_kaiheila(Mention)
    def _mention(m: Mention) -> MessageSegment:
        return MessageSegment.KMarkdown("(met)" + m.data["user_id"] + "(met)")

    @register_kaiheila(Reply)
    def _reply(r: Reply) -> MessageSegment:
        return MessageSegment.quote(r.data["message_id"])

    @register_target_extractor(PrivateMessageEvent)
    def _extract_private_msg_event(event: Event) -> TargetKaiheilaPrivate:
        assert isinstance(event, PrivateMessageEvent)
        return TargetKaiheilaPrivate(user_id=event.user_id)

    @register_target_extractor(ChannelMessageEvent)
    def _extract_channel_msg_event(event: Event) -> TargetKaiheilaChannel:
        assert isinstance(event, ChannelMessageEvent)
        return TargetKaiheilaChannel(channel_id=event.target_id)

    @register_convert_to_arg(adapter, SupportedPlatform.kaiheila_private)
    def _gen_private(target: PlatformTarget) -> Dict[str, Any]:
        assert isinstance(target, TargetKaiheilaPrivate)
        return {
            "user_id": target.user_id,
        }

    @register_convert_to_arg(adapter, SupportedPlatform.kaiheila_channel)
    def _gen_channel(target: PlatformTarget) -> Dict[str, Any]:
        assert isinstance(target, TargetKaiheilaChannel)
        return {
            "channel_id": target.channel_id,
        }

    @register_sender(SupportedAdapters.kaiheila)
    async def send(
        bot,
        msg: MessageFactory[MessageSegmentFactory],
        target,
        event,
        at_sender: bool,
        reply: bool,
    ):
        assert isinstance(bot, Bot)
        assert isinstance(target, (TargetKaiheilaPrivate, TargetKaiheilaChannel))

        if event:
            assert isinstance(event, MessageEvent)
            full_msg = assamble_message_factory(
                msg,
                Mention(event.get_user_id()),
                Reply(event.msg_id),
                at_sender,
                reply,
            )
        else:
            full_msg = msg

        message_to_send = Message()
        for message_segment_factory in full_msg:
            message_segment = await message_segment_factory.build(bot)
            message_to_send += message_segment

        sent_msg = await bot.send_msg(message=message_to_send, **target.arg_dict(bot))
        if sent_msg:
            sent_msg = sent_msg.dict()
            sent_msg["msg_id"] = str(sent_msg["msg_id"])
        return sent_msg

    @register_list_targets(SupportedAdapters.kaiheila)
    async def list_targets(bot: BaseBot) -> List[PlatformTarget]:
        assert isinstance(bot, Bot)

        targets = []

        async for guild in _unwrap_paging_api("guilds")(bot.guild_list)():
            guild: Guild
            async for channel in _unwrap_paging_api("channels")(bot.channel_list)(
                guild_id=guild.id_
            ):
                assert isinstance(channel, Channel)
                assert channel.id_
                target = TargetKaiheilaChannel(channel_id=channel.id_)
                targets.append(target)

        async for user_chat in _unwrap_paging_api("user_chats")(bot.userChat_list)():
            user_chat: UserChat
            assert user_chat.target_info and user_chat.target_info.id_
            target = TargetKaiheilaPrivate(user_id=user_chat.target_info.id_)
            targets.append(target)

        return targets

except ImportError:
    pass
except Exception as e:
    raise e
