from io import BytesIO
from pathlib import Path
from functools import partial
from typing import Any, Dict, Literal, cast

from nonebot.adapters import Event
from nonebot.adapters import Bot as BaseBot

from ..utils import SupportedAdapters
from ..types import Text, Image, Reply, Mention
from ..abstract_factories import (
    MessageFactory,
    register_ms_adapter,
    assamble_message_factory,
)
from ..registries import (
    Receipt,
    MessageId,
    TargetFeishuGroup,
    TargetFeishuPrivate,
    register_sender,
    register_target_extractor,
    register_message_id_getter,
)

try:
    import httpx
    from nonebot.adapters.feishu.message import At
    from nonebot.adapters.feishu import (
        Bot,
        Message,
        MessageEvent,
        MessageSegment,
        GroupMessageEvent,
        PrivateMessageEvent,
    )

    adapter = SupportedAdapters.feishu
    register_feishu = partial(register_ms_adapter, adapter)

    MessageFactory.register_adapter_message(adapter, Message)

    class FeishuMessageId(MessageId):
        adapter_name: Literal[adapter] = adapter
        message_id: str

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
        return At("at", {"user_id": m.data["user_id"]})

    @register_feishu(Reply)
    def _reply(r: Reply) -> MessageSegment:
        assert isinstance(mid := r.data["message_id"], FeishuMessageId)
        return MessageSegment("reply", {"message_id": mid.message_id})

    @register_target_extractor(PrivateMessageEvent)
    def _extract_private_msg_event(event: Event) -> TargetFeishuPrivate:
        assert isinstance(event, PrivateMessageEvent)
        return TargetFeishuPrivate(open_id=event.get_user_id())

    @register_target_extractor(GroupMessageEvent)
    def _extract_channel_msg_event(event: Event) -> TargetFeishuGroup:
        assert isinstance(event, GroupMessageEvent)
        return TargetFeishuGroup(chat_id=event.event.message.chat_id)

    class FeishuReceipt(Receipt):
        message_id: str
        adapter_name: Literal[adapter] = adapter
        data: Dict[str, Any]

        async def revoke(self):
            bot = cast(Bot, self._get_bot())
            params = {"method": "DELETE"}
            return await bot.call_api(f"im/v1/messages/{self.message_id}", **params)

        @property
        def raw(self) -> Any:
            return self.data

        def extract_message_id(self) -> FeishuMessageId:
            return FeishuMessageId(message_id=self.message_id)

    @register_message_id_getter(MessageEvent)
    def _(event: Event) -> FeishuMessageId:
        assert isinstance(event, MessageEvent)
        return FeishuMessageId(message_id=event.event.message.message_id)

    @register_sender(adapter)
    async def send(
        bot,
        msg: MessageFactory,
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
                Reply(FeishuMessageId(message_id=event.event.message.message_id)),
                at_sender,
                reply,
            )
        else:
            full_msg = msg

        reply_to_message_id = None
        message_to_send = Message()
        for message_segment_factory in full_msg:
            if isinstance(message_segment_factory, Reply):
                assert isinstance(
                    mid := message_segment_factory.data["message_id"], FeishuMessageId
                )
                reply_to_message_id = mid.message_id
                continue

            message_segment = await message_segment_factory.build(bot)
            message_to_send += message_segment

        msg_type, content = message_to_send.serialize()

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
            resp = await bot.call_api("im/v1/messages", **params)

        else:
            params = {
                "method": "POST",
                "body": {"content": content, "msg_type": msg_type},
            }
            resp = await bot.call_api(
                f"im/v1/messages/{reply_to_message_id}/reply", **params
            )
        message_id = resp["message_id"]
        return FeishuReceipt(bot_id=bot.self_id, message_id=message_id, data=resp)

except ImportError:
    pass
except Exception as e:
    raise e
