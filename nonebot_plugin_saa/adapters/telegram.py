from functools import partial
from io import BytesIO
from pathlib import Path
from typing import cast, Literal, Union, Optional, List, Sequence, Any

import anyio
from nonebot import logger
from nonebot.adapters import Bot, Event
from nonebot.adapters.telegram.model import MessageEntity, InputMedia


from ..types import Text, Image, Reply, Mention
from ..utils import (
    MessageFactory,
    SupportedAdapters,
    TargetTelegramForum,
    TargetTelegramCommon,
    MessageSegmentFactory,
    register_sender,
    register_get_bot_id,
    register_ms_adapter,
    assamble_message_factory,
    register_target_extractor, Receipt, get_bot_id,
)

try:
    from nonebot.adapters.telegram import Bot as BotTG
    from nonebot.adapters.telegram.message import File, Entity, UnCombinFile
    from nonebot.adapters.telegram import Message, MessageSegment
    from nonebot.adapters.telegram.event import (
        MessageEvent,
        ChannelPostEvent,
        GroupMessageEvent,
        PrivateMessageEvent,
        ForumTopicMessageEvent,
    )

    adapter = SupportedAdapters.telegram
    register_telegram = partial(register_ms_adapter, adapter)

    MessageFactory.register_adapter_message(SupportedAdapters.telegram, Message)


    def build_entities_form_msg(
        message: Sequence[MessageSegment]
    ) -> Optional[List[MessageEntity]]:
        return (
            (
                [
                    MessageEntity(
                        type=entity.type,
                        offset=sum(map(len, message[:i])),
                        length=len(entity.data["text"]),
                        url=entity.data.get("url"),
                        user=entity.data.get("user"),
                        language=entity.data.get("language"),
                    )
                    for i, entity in enumerate(message)
                    if entity.is_text() and entity.type != "text"
                ]
                or None
            )
            if message
            else None
        )


    @register_telegram(Text)
    def _text(t: Text) -> MessageSegment:
        return Entity.text(t.data["text"])


    @register_telegram(Image)
    async def _image(i: Image) -> MessageSegment:
        image = i.data["image"]
        if isinstance(image, Path):
            image = await anyio.Path(image).read_bytes()
        if isinstance(image, BytesIO):
            image = image.getvalue()
        return File.photo(image)


    @register_telegram(Mention)
    async def _mention(m: Mention) -> MessageSegment:
        user_id = m.data["user_id"]
        return (
            Entity.mention(f"{user_id} ")
            if user_id.startswith("@")
            else Entity.text_link("用户 ", f"tg://user?id={user_id}")
        )


    @register_telegram(Reply)
    async def _reply(r: Reply) -> MessageSegment:
        return MessageSegment("reply", cast(dict, r.data))


    @register_target_extractor(PrivateMessageEvent)
    @register_target_extractor(GroupMessageEvent)
    @register_target_extractor(ChannelPostEvent)
    def _extract_private_msg_event(event: Event) -> TargetTelegramCommon:
        assert isinstance(event, MessageEvent)
        return TargetTelegramCommon(chat_id=event.chat.id)


    @register_target_extractor(ForumTopicMessageEvent)
    def _extract_forum_msg_event(event: Event) -> TargetTelegramForum:
        assert isinstance(event, ForumTopicMessageEvent)
        return TargetTelegramForum(
            chat_id=event.chat.id,
            message_thread_id=event.message_thread_id,
        )


    def build_mention_from_event(event: MessageEvent) -> MessageSegment:
        # has user
        if isinstance(
            event,
            (PrivateMessageEvent, GroupMessageEvent, ForumTopicMessageEvent),
        ):
            user = event.from_

            # has username
            if username := user.username:
                return Entity.mention(f"@{username} ")

            # no username
            last_name = f" {user.last_name}" if user.last_name else ""
            return Entity.text_link(
                f"{user.first_name}{last_name} ",
                f"tg://user?id={user.id}",
            )

        # no user
        return Entity.text("")


    class TelegramReceipt(Receipt):
        sent_msg: Any
        sent_type: Literal["text", "image"]
        chat_id: Union[str, int]
        reply_to_msg_id: Optional[Union[str, int]]
        mention_user_id: Optional[Union[str, int]]
        adapter_name = adapter

        @property
        def message_id(self) -> Union[str, list[str]]:
            if isinstance(self.sent_msg, list):
                return [f'{msg.message_id}.{self.chat_id}' for msg in self.sent_msg]
            else:
                return f'{self.sent_msg.message_id}.{self.chat_id}'

        async def revoke(self):
            bot = self._get_bot()

            async def del_msg_with_retry(msg_id):
                retry = 3
                error = Exception("Unknown Error Deleting Telegram message")
                while retry > 0:
                    try:
                        return await bot.delete_message(
                            chat_id=self.chat_id, message_id=msg_id
                        )
                    except Exception as e:
                        error = e
                        pass
                raise error

            if isinstance(self.sent_msg, list):
                for message_id in self.message_id:
                    await del_msg_with_retry(message_id.split(".")[0])
            else:
                await del_msg_with_retry(self.message_id.split(".")[0])

        async def edit(self, msg: MessageFactory[MessageSegmentFactory], at_sender=False, reply=False):  # noqa: E501
            bot = self._get_bot()
            if isinstance(msg, MessageSegmentFactory):
                msg = MessageFactory([msg])
            message_to_send = Message()
            for message_segment_factory in msg:
                if isinstance(message_segment_factory, Reply):
                    self.reply_to_msg_id = message_segment_factory.data["message_id"]
                else:
                    message_segment = await message_segment_factory.build(bot)
                    message_to_send += message_segment
            if self.reply_to_msg_id and reply:
                message_to_send = await Reply(self.reply_to_msg_id).build(bot) + message_to_send
            if self.mention_user_id and at_sender:
                message_to_send = await MessageFactory(self.mention_user_id).build(bot) + message_to_send  # noqa: E501

            # 处理 Message 的编辑
            # 分离各类型 seg
            entities = Message(x for x in message_to_send if isinstance(x, Entity))
            images = Message(
                x
                for x in message_to_send
                if isinstance(x, File) and not isinstance(message_to_send, UnCombinFile)
            )

            if self.sent_type == "image":
                if not images:
                    raise Exception("Saa在编辑Tg的含Image信息时,仅能编辑为含少于等于原Image数量的信息")
                if isinstance(self.sent_msg, list):
                    if len(images) > len(self.sent_msg):
                        logger.error("Saa在编辑Tg的含Image信息时,仅能编辑为含少于等于原Image数量的信息")
                    message_ids = self.message_id
                    for index, message_id in enumerate(message_ids):
                        if index < len(images):
                            await bot.edit_message_media(
                                media=InputMedia(type=images[index].type, media=images[index].data["file"],
                                                 caption=str(entities),
                                                 caption_entities=build_entities_form_msg(message_to_send)),
                                chat_id=self.chat_id,
                                message_id=message_ids[index].split(".")[0],
                            )
                        else:
                            to_del_receipt = self.copy()
                            to_del_receipt.sent_msg = self.sent_msg[index:]
                            await to_del_receipt.revoke()
                            self.sent_msg = self.sent_msg[:index]
                            break
                else:
                    if len(images) > 1:
                        logger.error("Saa在编辑消息时对于单图片的Tg消息,也只能编辑为单图片的消息")
                    await bot.edit_message_media(
                        media=InputMedia(type=images[0].type, media=images[0].data["file"],
                                         caption=str(entities),
                                         caption_entities=build_entities_form_msg(message_to_send)),
                        chat_id=self.chat_id,
                        message_id=self.message_id.split(".")[0],
                    )
            else:
                if images:
                    raise Exception("Saa在编辑Tg的纯Text信息时,仅能编辑为纯Text信息")
                return await bot.edit_message_text(
                    chat_id=self.chat_id,
                    message_id=self.message_id.split(".")[0],
                    text=str(entities),
                    entities=build_entities_form_msg(message_to_send),
                )


    @register_sender(SupportedAdapters.telegram)
    async def send(
        bot,
        msg: MessageFactory[MessageSegmentFactory],
        target,
        event,
        at_sender: bool,
        reply: bool,
    ):
        assert isinstance(bot, BotTG)
        assert isinstance(target, (TargetTelegramCommon, TargetTelegramForum))

        if event:
            assert isinstance(event, MessageEvent)
            full_msg = assamble_message_factory(
                msg,
                (
                    None
                    if isinstance(event, ChannelPostEvent)
                    else Mention(event.get_user_id())
                ),
                Reply(event.message_id),
                at_sender,
                reply,
            )
        else:
            full_msg = msg
        params = {"sent_type": "text", "mention_user_id": event.get_user_id(), "reply_to_msg_id": event.message_id}

        message_to_send = Message()
        reply_to_message_id = None
        for message_segment_factory in full_msg:
            if isinstance(message_segment_factory, Image):
                params["sent_type"] = "image"
            if isinstance(message_segment_factory, Reply):
                reply_to_message_id = int(message_segment_factory.data["message_id"])
                continue

            if (
                event
                and isinstance(message_segment_factory, Mention)
                and message_segment_factory.data["user_id"] == event.get_user_id()
            ):
                message_segment = build_mention_from_event(event)
            else:
                message_segment = await message_segment_factory.build(bot)

            message_to_send += message_segment

        chat_id = target.chat_id
        message_thread_id = (
            target.message_thread_id
            if isinstance(target, TargetTelegramForum)
            else None
        )
        sent_msg = await bot.send_to(
            chat_id,
            message_to_send,
            message_thread_id=message_thread_id,
            reply_to_message_id=reply_to_message_id,
        )
        return TelegramReceipt(bot_id=get_bot_id(bot), sent_msg=sent_msg, message_id=sent_msg.message_id,
                               chat_id=chat_id, **params)


    @register_get_bot_id(adapter)
    def _get_id(bot: Bot):
        assert isinstance(bot, BotTG)
        return bot.self_id

    @register_get_bot_id(adapter)
    def _get_id(bot: Bot):
        assert isinstance(bot, BotTG)
        return bot.self_id

except ImportError:
    pass
except Exception:
    raise
