from io import BytesIO
from pathlib import Path
from functools import partial
from typing import Any, Union, Optional, cast

import anyio
from nonebot.adapters import Event
from pydantic import BaseModel

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
    register_target_extractor,
)

try:
    from nonebot.adapters.telegram import Bot as BotTG
    from nonebot.adapters.telegram.message import File, Entity
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

    class FakeChat(BaseModel):
        id: Union[str, int]  # noqa: A003

    class FakeEvent(BaseModel):
        chat: FakeChat
        message_thread_id: Optional[int]

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

    def build_fake_event(
        target: Union[TargetTelegramCommon, TargetTelegramForum],
    ) -> FakeEvent:
        return FakeEvent(
            chat=FakeChat(id=target.chat_id),
            message_thread_id=(
                target.message_thread_id
                if isinstance(target, TargetTelegramForum)
                else None
            ),
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

        await bot.send(
            event or cast(Any, build_fake_event(target)),
            message=message_to_send,
            reply_to_message_id=reply_to_message_id,
        )

except ImportError:
    pass
except Exception:
    raise
