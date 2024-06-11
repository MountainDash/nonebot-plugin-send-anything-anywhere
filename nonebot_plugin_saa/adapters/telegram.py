import asyncio
from io import BytesIO
from pathlib import Path
from functools import partial
from typing import TYPE_CHECKING, Union, Literal, Optional, cast

import anyio
from nonebot import logger

from ..types import Text, Image, Reply, Mention, MentionAll
from ..utils import SupportedAdapters, type_message_id_check
from ..abstract_factories import (
    MessageFactory,
    register_ms_adapter,
    assamble_message_factory,
)
from ..registries import (
    Receipt,
    MessageId,
    PlatformTarget,
    TargetTelegramForum,
    TargetTelegramCommon,
    register_sender,
    register_target_extractor,
    register_message_id_getter,
)

if TYPE_CHECKING:
    from nonebot.adapters import Bot as BaseBot
    from nonebot.adapters import Event as BaseEvent

try:
    from nonebot.adapters.telegram import Bot as BotTG
    from nonebot.adapters.telegram.message import File as TGFile
    from nonebot.adapters.telegram import Message, MessageSegment
    from nonebot.adapters.telegram.message import Reply as TGReply
    from nonebot.adapters.telegram.message import Entity as TGEntity
    from nonebot.adapters.telegram.model import Message as MessageModel
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

    class TelegramMessageId(MessageId):
        adapter_name: Literal[adapter] = adapter
        message_id: int
        chat_id: Union[int, str, None] = None

    @register_telegram(Text)
    def _text(t: Text) -> MessageSegment:
        return TGEntity.text(t.data["text"])

    @register_telegram(Image)
    async def _image(i: Image) -> MessageSegment:
        image = i.data["image"]
        if isinstance(image, Path):
            image = await anyio.Path(image).read_bytes()
        if isinstance(image, BytesIO):
            image = image.getvalue()
        return TGFile.photo(image)

    @register_telegram(Mention)
    async def _mention(m: Mention) -> MessageSegment:
        user_id = m.data["user_id"]
        return (
            TGEntity.mention(f"{user_id} ")
            if user_id.startswith("@")
            else TGEntity.text_link("用户 ", f"tg://user?id={user_id}")
        )

    @register_telegram(MentionAll)
    def _mention_all(m: MentionAll) -> MessageSegment:
        logger.warning("Telegram does not support @everyone members yet, ignored.")
        if text := m.data.get("special_fallback", {}).get(adapter):
            return TGEntity.text(text)

        if text := m.data["fallback"]:
            return TGEntity.text(text)

        # tg 一般是国外平台，所以默认英文
        if m.data["online_only"]:
            return TGEntity.text("@online ")

        return TGEntity.text("@everyone ")

    @register_telegram(Reply)
    async def _reply(r: Reply) -> MessageSegment:
        mid = type_message_id_check(TelegramMessageId, r.data["message_id"])
        return TGReply.reply(mid.message_id, mid.chat_id)

    @register_target_extractor(PrivateMessageEvent)
    @register_target_extractor(GroupMessageEvent)
    @register_target_extractor(ChannelPostEvent)
    def _extract_private_msg_event(event: "BaseEvent") -> TargetTelegramCommon:
        assert isinstance(event, MessageEvent)
        return TargetTelegramCommon(chat_id=event.chat.id)

    @register_target_extractor(ForumTopicMessageEvent)
    def _extract_forum_msg_event(event: "BaseEvent") -> TargetTelegramForum:
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
                return TGEntity.mention(f"@{username} ")

            # no username
            last_name = f" {user.last_name}" if user.last_name else ""
            return TGEntity.text_link(
                f"{user.first_name}{last_name} ",
                f"tg://user?id={user.id}",
            )

        # no user
        return TGEntity.text("")

    class TelegramReceipt(Receipt):
        chat_id: Union[int, str]
        messages: list[MessageModel]
        adapter_name: Literal[adapter] = adapter

        async def revoke(self):
            bot = cast(BotTG, self._get_bot())
            return await asyncio.gather(
                *(
                    bot.delete_message(chat_id=self.chat_id, message_id=x.message_id)
                    for x in self.messages
                ),
            )

        @property
        def raw(self):
            return self.messages

        def extract_message_id(self, index: int = 0) -> TelegramMessageId:
            """从 Receipt 中提取 MessageId

            Args:
                index (int, optional): 默认为0, 即提取第一条消息的 MessageId.
            """
            return TelegramMessageId(
                message_id=self.messages[index].message_id,
                chat_id=self.chat_id,
            )

    @register_message_id_getter(MessageEvent)
    def _(event: "BaseEvent"):
        assert isinstance(event, MessageEvent)
        return TelegramMessageId(
            message_id=event.message_id,
            chat_id=event.chat.id,
        )

    @register_sender(SupportedAdapters.telegram)
    async def send(
        bot: "BaseBot",
        msg: MessageFactory,
        target: "PlatformTarget",
        event: Optional["BaseEvent"],
        at_sender: bool,
        reply: bool,
    ) -> TelegramReceipt:
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
                Reply(
                    TelegramMessageId(
                        message_id=event.message_id,
                        chat_id=event.chat.id,
                    ),
                ),
                at_sender,
                reply,
            )
        else:
            full_msg = msg

        message_to_send = Message()
        for message_segment_factory in full_msg:
            if (
                isinstance(message_segment_factory, Mention)
                and event
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
        message_sent = cast(
            Union[MessageModel, list[MessageModel]],
            await bot.send_to(
                chat_id,
                message_to_send,
                message_thread_id=message_thread_id,
            ),
        )
        return TelegramReceipt(
            bot_id=bot.self_id,
            chat_id=chat_id,
            messages=message_sent if isinstance(message_sent, list) else [message_sent],
        )

except ImportError:
    pass
except Exception:
    raise
