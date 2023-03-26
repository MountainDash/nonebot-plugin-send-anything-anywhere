import json
from functools import partial
from typing import Any

from nonebot import logger
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
    register_convert_to_arg,
    assamble_message_factory,
    register_target_extractor,
)
from ..utils.platform_send_target import TargetKaiheilaPrivate, TargetKaiheilaChannel

try:
    from nonebot.adapters.kaiheila import Bot
    from nonebot.adapters.kaiheila.message import Message, MessageSegment
    from nonebot.adapters.kaiheila.event import (
        MessageEvent,
        ChannelMessageEvent,
        PrivateMessageEvent,
    )

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
        return TargetKaiheilaChannel(user_id=event.author_id,
                                     channel_id=event.target_id,
                                     guild_id=event.extra.guild_id)


    @register_convert_to_arg(adapter, SupportedPlatform.kaiheila_private)
    def _gen_private(target: PlatformTarget) -> dict[str, Any]:
        assert isinstance(target, TargetKaiheilaPrivate)
        return {
            "user_id": target.user_id,
        }


    @register_convert_to_arg(adapter, SupportedPlatform.kaiheila_channel)
    def _gen_group(target: PlatformTarget) -> dict[str, Any]:
        assert isinstance(target, TargetKaiheilaChannel)
        return {
            "user_id": target.user_id,
            "channel_id": target.channel_id,
        }


    _card_template = {
        "type": "card",
        "theme": "none",
        "size": "lg",
        "modules": []
    }


    def _convert_to_card_message(msg: Message) -> MessageSegment:
        cards = []

        modules = []

        for seg in msg:
            if seg.type == 'card':
                if len(modules) != 0:
                    cards.append({
                        **_card_template,
                        "modules": modules
                    })
                    modules = []

                cards.extend(json.loads(seg.data["content"]))
            elif seg.type == 'text':
                modules.append({
                    "type": "section",
                    "text": {
                        "type": "plain-text",
                        "content": seg.data["content"]
                    }
                })
            elif seg.type == 'image':
                modules.append({
                    "type": "container",
                    "elements": [
                        {
                            "type": "image",
                            "src": seg.data["file_key"]
                        }
                    ]
                })
            else:
                logger.warning("Ignored unknown message segment type: " + seg.type)

        if len(modules) != 0:
            cards.append({
                **_card_template,
                "modules": modules
            })

        return MessageSegment.Card(json.dumps(cards))


    def _handle_msg(msg: Message) -> Message:
        """如果消息由多个消息段组成，转化为卡片消息发送"""
        msg.reduce()

        real_msg = msg
        if len(msg) != 0 and msg[0].type == 'quote':
            real_msg = msg[1:]

        if len(real_msg) <= 1:
            return msg
        else:
            ret_msg = Message(_convert_to_card_message(real_msg))
            if msg[0].type == 'quote':
                ret_msg.insert(0, msg[0])
            return ret_msg


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
        assert isinstance(target, TargetKaiheilaPrivate | TargetKaiheilaChannel)

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

        message_to_send = _handle_msg(message_to_send)
        await bot.send_msg(message=message_to_send, **target.arg_dict(bot))

except ImportError:
    pass
except Exception as e:
    raise e
