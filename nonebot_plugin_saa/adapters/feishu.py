from functools import partial
from io import BytesIO
from typing import cast

from nonebot.adapters import Bot as BaseBot
from nonebot.adapters import Event

from ..types import Image, Mention, Reply, Text
from ..utils import (
    MessageFactory,
    MessageSegmentFactory,
    SupportedAdapters,
    assamble_message_factory,
    register_ms_adapter,
    register_sender,
    register_target_extractor,
)
from ..utils.platform_send_target import TargetFeishuGroup, TargetFeishuPrivate

try:
    from nonebot.adapters.feishu import (
        Bot,
        GroupMessageEvent,
        Message,
        MessageEvent,
        MessageSegment,
        MessageSerializer,
        PrivateMessageEvent,
    )

    adapter = SupportedAdapters.feishu
    register_feishu = partial(register_ms_adapter, adapter)

    MessageFactory.register_adapter_message(SupportedAdapters.feishu, Message)

    @register_feishu(Text)
    def _text(t: Text) -> MessageSegment:
        return MessageSegment.text(t.data["text"])

    @register_feishu(Image)
    async def _image(i: Image, bot: BaseBot) -> MessageSegment:
        if not isinstance(bot, Bot):
            raise TypeError(f"Unsupported type of bot: {type(bot)}")

        image = i.data["image"]
        if isinstance(image, BytesIO):
            image = image.getvalue()

        data = {"image_type": "message"}
        files = {"image": open(image, "rb")}
        params = {"method": "POST", "data": data, "files": files}
        result = await bot.call_api("im/v1/images", **params)
        file_key = result["image_key"]
        return MessageSegment.image(file_key)

    @register_feishu(Mention)
    def _mention(m: Mention) -> MessageSegment:
        return MessageSegment.at(m.data["user_id"])

    @register_feishu(Reply)
    def _reply(r: Reply) -> MessageSegment:
        return MessageSegment("reply", cast(dict, r.data))

    @register_target_extractor(PrivateMessageEvent)
    def _extract_private_msg_event(event: Event) -> TargetFeishuPrivate:
        assert isinstance(event, PrivateMessageEvent)
        return TargetFeishuPrivate(open_id=event.get_user_id())

    @register_target_extractor(GroupMessageEvent)
    def _extract_channel_msg_event(event: Event) -> TargetFeishuGroup:
        assert isinstance(event, GroupMessageEvent)
        return TargetFeishuGroup(chat_id=event.event.message.chat_id)

    @register_sender(SupportedAdapters.feishu)
    async def send(
        bot,
        msg: MessageFactory[MessageSegmentFactory],
        target,
        event,
        at_sender: bool,
        reply: bool,
    ):
        assert isinstance(bot, Bot)
        assert isinstance(target, (TargetFeishuPrivate, TargetFeishuGroup))

        if event:
            assert isinstance(event, MessageEvent)
            full_msg = assamble_message_factory(
                msg,
                (
                    Mention(event.get_user_id())
                    if isinstance(event, GroupMessageEvent)
                    else None
                ),
                Reply(event.event.message.message_id),
                at_sender,
                reply,
            )
        else:
            full_msg = msg

        reply_to_message_id = None
        message_to_send = Message()
        for message_segment_factory in full_msg:
            if isinstance(message_segment_factory, Reply):
                reply_to_message_id = message_segment_factory.data["message_id"]
                continue

            message_segment = await message_segment_factory.build(bot)
            message_to_send += message_segment

        msg_type, content = MessageSerializer(message_to_send).serialize()

        if reply_to_message_id is None:
            if isinstance(target, TargetFeishuGroup):
                receive_id, receive_id_type = target.chat_id, "chat_id"
            else:
                receive_id, receive_id_type = target.open_id, "open_id"
            params = {
                "method": "POST",
                "query": {"receive_id_type": receive_id_type},
                "body": {
                    "receive_id": receive_id,
                    "content": content,
                    "msg_type": msg_type,
                },
            }
            await bot.call_api("im/v1/messages", **params)

        else:
            params = {
                "method": "POST",
                "body": {"content": content, "msg_type": msg_type},
            }
            await bot.call_api(f"im/v1/messages/{reply_to_message_id}/reply", **params)

except ImportError:
    pass
except Exception as e:
    raise e
