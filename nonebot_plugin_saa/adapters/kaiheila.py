from functools import partial
from typing import Any, Dict, List, Literal, TypedDict, cast, Union, Optional


from nonebot.adapters import Bot as BaseBot
from nonebot.adapters import Event

from ..types import Text, Image, Reply, Mention
from ..utils import (
    Receipt,
    MessageFactory,
    PlatformTarget,
    SupportedAdapters,
    SupportedPlatform,
    MessageSegmentFactory,
    get_bot_id,
    register_sender,
    register_get_bot_id,
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
    from nonebot.adapters.kaiheila.message import (
        Message,
        MessageSegment,
        MessageSerializer,
    )
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


    # https://developer.kookapp.cn/doc/http/message#%E5%8F%91%E9%80%81%E9%A2%91%E9%81%93%E8%81%8A%E5%A4%A9%E6%B6%88%E6%81%AF



    class RawResp(TypedDict):
        msg_id: str
        msg_timestamp: int
        nonce: str


    class KaiheilaReceipt(Receipt):
        sent_msg: RawResp
        message_id: str
        type: Literal["group", "private"]
        target_id: Union[str, int]
        reply_to_msg_id: Optional[Union[str, int]]
        mention_user_id: Optional[Union[str, int]]
        adapter_name = adapter

        async def revoke(self):
            if self.type == "group":
                return await cast(Bot, self._get_bot()).message_delete(
                    msg_id=self.message_id
                )
            else:
                return await cast(Bot, self._get_bot()).directMessage_delete(
                    msg_id=self.message_id
                )

        async def edit(self, msg, at_sender=False, reply=False):
            bot = self._get_bot()
            if at_sender:
                msg = Mention(user_id=self.mention_user_id) + msg
            if reply:
                msg = Reply(message_id=self.reply_to_msg_id) + msg

            message_to_send = Message()
            for message_segment_factory in msg:
                message_segment = await message_segment_factory.build(bot)
                message_to_send += message_segment

            params = {"msg_id": str(self.message_id)}
            # type & content
            if isinstance(message_to_send, Message):
                new_message = Message()
                # 提取message中的quote消息段
                for seg in message_to_send:
                    if seg.type == "quote":
                        params["quote"] = seg.data["msg_id"]
                    else:
                        new_message.append(seg)
                params["type"], params["content"] = MessageSerializer(
                    new_message
                ).serialize()
            elif isinstance(message_to_send, MessageSegment):
                params["type"], params["content"] = MessageSerializer(
                    Message(message_to_send)
                ).serialize()
            else:
                raise ValueError("message为空或有误")

            # target_id & api
            params["target_id"] = self.target_id
            if self.type == "group":
                api = "message/update"
            else:
                params["target_id"] = self.target_id
                api = "direct-message/update"

            return await bot.call_api(api, **params)

        @property
        def raw(self) -> RawResp:
            return self.sent_msg


    @register_sender(SupportedAdapters.kaiheila)
    async def send(
        bot,
        msg: MessageFactory[MessageSegmentFactory],
        target,
        event: Event,
        at_sender: bool,
        reply: bool,
    ) -> KaiheilaReceipt:
        assert isinstance(bot, Bot)
        assert isinstance(target, (TargetKaiheilaPrivate, TargetKaiheilaChannel))

        params = {}
        if event.get_event_name().startswith("message.group"):
            params["type"] = "group"
            params["target_id"] = target.channel_id
        else:
            params["type"] = "private"
            params["target_id"] = target.user_id

        params["mention_user_id"] = event.get_user_id()
        params["reply_to_msg_id"] = event.msg_id

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

        resp = await bot.send_msg(message=message_to_send, **target.arg_dict(bot))
        return KaiheilaReceipt(
            bot_id=get_bot_id(bot),
            sent_msg=cast(RawResp, resp),
            message_id=resp.msg_id,
            **params,
        )


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



    @register_get_bot_id(adapter)
    def _get_id(bot: BaseBot):
        assert isinstance(bot, Bot)
        return bot.self_id

except ImportError:
    pass
except Exception as e:
    raise e
