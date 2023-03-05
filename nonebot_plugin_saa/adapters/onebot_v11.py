from functools import partial
from typing import Literal, Optional

from nonebot.adapters import Event

from ..types import Text, Image, Reply, Mention
from ..utils import (
    MessageFactory,
    SupportedAdapters,
    AbstractSendTarget,
    MessageSegmentFactory,
    register_sender,
    register_ms_adapter,
    assamble_message_factory,
    register_target_extractor,
)


class SendTargetOneBot11(AbstractSendTarget):
    adapter_type: Literal[SupportedAdapters.onebot_v11] = SupportedAdapters.onebot_v11
    group_id: Optional[int] = None
    user_id: Optional[int] = None
    message_type: Optional[Literal["private", "group"]] = None


try:
    from nonebot.adapters.onebot.v11 import Bot as BotOB11
    from nonebot.adapters.onebot.v11.message import Message, MessageSegment
    from nonebot.adapters.onebot.v11 import (
        MessageEvent,
        GroupMessageEvent,
        PrivateMessageEvent,
    )

    adapter = SupportedAdapters.onebot_v11
    register_onebot_v11 = partial(register_ms_adapter, adapter)

    MessageFactory.register_adapter_message(SupportedAdapters.onebot_v11, Message)

    @register_onebot_v11(Text)
    def _text(t: Text) -> MessageSegment:
        return MessageSegment.text(t.data["text"])

    @register_onebot_v11(Image)
    async def _image(i: Image) -> MessageSegment:
        return MessageSegment.image(i.data["image"])

    @register_onebot_v11(Mention)
    async def _mention(m: Mention) -> MessageSegment:
        return MessageSegment.at(m.data["user_id"])

    @register_onebot_v11(Reply)
    async def _reply(r: Reply) -> MessageSegment:
        return MessageSegment.reply(int(r.data["message_id"]))

    @register_target_extractor(PrivateMessageEvent)
    def _extract_private_msg_event(event: Event) -> SendTargetOneBot11:
        assert isinstance(event, PrivateMessageEvent)
        return SendTargetOneBot11(
            message_type="private",
            user_id=event.user_id,
        )

    @register_target_extractor(GroupMessageEvent)
    def _extract_group_msg_event(event: Event) -> SendTargetOneBot11:
        assert isinstance(event, GroupMessageEvent)
        return SendTargetOneBot11(message_type="group", group_id=event.group_id)

    @register_sender(SupportedAdapters.onebot_v11)
    async def send(
        bot,
        msg: MessageFactory[MessageSegmentFactory],
        target,
        event,
        at_sender: bool,
        reply: bool,
    ):
        assert isinstance(bot, BotOB11)
        assert isinstance(target, SendTargetOneBot11)
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
        await bot.send_msg(message=message_to_send, **target.arg_dict())

except ImportError:
    pass
except Exception as e:
    raise e
