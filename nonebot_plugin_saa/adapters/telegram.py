from functools import partial
from io import BytesIO
from pathlib import Path
from typing import cast, Sequence, Optional, List

import anyio
import nonebot
from nonebot import logger
from nonebot.adapters import Event
from nonebot.adapters.telegram.model import InputMedia, MessageEntity

from ..types import Text, Image, Reply, Mention
from ..utils import (
    MessageFactory,
    SupportedAdapters,
    TargetTelegramForum,
    TargetTelegramCommon,
    MessageSegmentFactory,
    register_sender,
    register_ms_adapter,
    assamble_message_factory,
    register_target_extractor, SupportedEditorAdapters, register_editor,
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


    async def process_data(bot, event, msg, at_sender, reply):
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

        reply_to_message_id = None
        message_to_send = Message()
        for message_segment_factory in full_msg:
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
        return message_to_send, reply_to_message_id


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

        message_to_send, reply_to_message_id = await process_data(bot, event, msg, at_sender, reply)  # noqa: E501

        message_thread_id = (
            target.message_thread_id
            if isinstance(target, TargetTelegramForum)
            else None
        )
        await bot.send_to(
            target.chat_id,
            message_to_send,
            message_thread_id=message_thread_id,
            reply_to_message_id=reply_to_message_id,
        )


    @register_editor(SupportedEditorAdapters.telegram)
    async def edit(
        bot: nonebot.adapters.telegram.Bot,
        msg: MessageFactory[MessageSegmentFactory],
        target,
        message_target,
        event,
        at_sender: bool,
        reply: bool,
    ):
        message_to_send, reply_to_message_id = await process_data(bot, event, msg, at_sender, reply)  # noqa: E501

        # 处理 Message 的编辑
        # 分离各类型 seg
        entities = Message(x for x in message_to_send if isinstance(x, Entity))
        files = Message(
            x
            for x in message_to_send
            if isinstance(x, File) and not isinstance(message_to_send, UnCombinFile)
        )

        if files:
            if len(files) > 1:
                logger.error("Telegram的edit方法受限于官方api限制,目前只能编辑一个图片,无法实现多个")
            # 只能单个图片
            await bot.edit_message_media(
                media=InputMedia(type=files[0].type, media=files[0].data["file"], caption=str(entities),
                                 caption_entities=build_entities_form_msg(message_to_send)),
                chat_id=target.chat_id,
                message_id=message_target.message_id,
            )
        else:
            await bot.edit_message_text(
                chat_id=target.chat_id,
                message_id=message_target.message_id,
                text=str(entities),
                entities=build_entities_form_msg(message_to_send),
            )

except ImportError:
    pass
except Exception:
    raise
