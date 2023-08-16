from functools import partial
from io import BytesIO
from pathlib import Path
from typing import cast, Any, Union, Optional

from nonebot.adapters import Bot as BaseBot
from nonebot.adapters import Event

from ..types import Text, Image, Reply, Mention
from ..utils import (
    MessageFactory,
    SupportedAdapters,
    MessageSegmentFactory,
    register_sender,
    register_get_bot_id,
    register_ms_adapter,
    assamble_message_factory,
    register_target_extractor, Receipt, get_bot_id,
)
from ..utils.platform_send_target import TargetFeishuGroup, TargetFeishuPrivate

try:
    import httpx
    from nonebot.adapters.feishu import (
        Bot,
        Message,
        MessageEvent,
        MessageSegment,
        GroupMessageEvent,
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
        if isinstance(image, str):
            async with httpx.AsyncClient() as client:
                resp = await client.get(image, timeout=10, follow_redirects=True)
                resp.raise_for_status()
                image = resp.content
        elif isinstance(image, Path):
            image = image.read_bytes()
        elif isinstance(image, BytesIO):
            image = image.getvalue()

        data = {"image_type": "message"}
        files = {"image": ("file", image)}
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


    class FeishuReceipt(Receipt):
        sent_msg: Optional[dict]
        message_id: Union[str, int]
        adapter_name = adapter

        async def revoke(self):
            return await self._get_bot().call_api(f"im/v1/messages/{self.message_id}", **{
                "method": "DELETE",
            })

        @property
        def raw(self) -> Any:
            return self.sent_msg


    @register_sender(SupportedAdapters.feishu)
    async def send(
        bot,
        msg: MessageFactory[MessageSegmentFactory],
        target,
        event,
        at_sender: bool,
        reply: bool,
    ) -> FeishuReceipt:
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
            sent_msg = await bot.call_api("im/v1/messages", **params)

        else:
            params = {
                "method": "POST",
                "body": {"content": content, "msg_type": msg_type},
            }
            sent_msg = await bot.call_api(f"im/v1/messages/{reply_to_message_id}/reply", **params)  # noqa: E501
        return FeishuReceipt(bot_id=get_bot_id(bot), sent_msg=sent_msg, message_id=sent_msg["message_id"])


    @register_get_bot_id(adapter)
    def _get_id(bot: BaseBot):
        assert isinstance(bot, Bot)
        return bot.self_id

    @register_get_bot_id(adapter)
    def _get_id(bot: BaseBot):
        assert isinstance(bot, Bot)
        return bot.self_id

except ImportError:
    pass
except Exception as e:
    raise e
