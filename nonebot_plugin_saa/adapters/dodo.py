from functools import partial
from contextlib import suppress
from typing import Any, Dict, List, Literal, Optional, cast

from nonebot import logger
from nonebot.adapters import Event
from nonebot.drivers import Request
from nonebot.adapters import Bot as BaseBot

from ..types import Text, Image, Reply, Mention
from ..auto_select_bot import register_list_targets
from ..utils import SupportedAdapters, SupportedPlatform
from ..abstract_factories import (
    MessageFactory,
    MessageSegmentFactory,
    register_ms_adapter,
    assamble_message_factory,
)
from ..registries import (
    Receipt,
    MessageId,
    PlatformTarget,
    TargetDoDoChannel,
    TargetDoDoPrivate,
    register_sender,
    register_convert_to_arg,
    register_target_extractor,
    register_message_id_getter,
)

with suppress(ImportError):
    from nonebot.adapters.dodo import Bot as BotDodo
    from nonebot.adapters.dodo.models import MessageBody
    from nonebot.adapters.dodo.message import Message, MessageSegment
    from nonebot.adapters.dodo.event import (
        MessageEvent,
        GiftSendEvent,
        ChannelArticleEvent,
        ChannelMessageEvent,
        MessageReactionEvent,
        PersonalMessageEvent,
        CardMessageFormSubmitEvent,
        CardMessageListSubmitEvent,
        ChannelArticleCommentEvent,
        CardMessageButtonClickEvent,
        ChannelVoiceMemberJoinEvent,
        ChannelVoiceMemberLeaveEvent,
    )

    adapter = SupportedAdapters.dodo
    register_dodo = partial(register_ms_adapter, adapter)

    class DodoMessageId(MessageId):
        adapter_name: Literal[adapter] = adapter

        message_id: str
        reason: Optional[None] = None

    @register_message_id_getter(MessageEvent)
    def _get_message_id(event: Event) -> DodoMessageId:
        assert isinstance(event, MessageEvent)
        return DodoMessageId(message_id=event.message_id)

    @register_dodo(Text)
    def _text(text: Text) -> MessageSegment:
        return MessageSegment.text(text.data["text"])

    @register_dodo(Image)
    async def _image(image: Image, bot: BaseBot) -> MessageSegment:
        if not isinstance(bot, BotDodo):
            raise TypeError(f"Unsupported type of bot: {type(bot)}")

        file = image.data["image"]
        if isinstance(file, str):
            # 要求必须是官方链接，因此需要下载一遍
            req = Request("GET", file, timeout=10)
            resp = await bot.adapter.request(req)
            if resp.status_code != 200:
                raise RuntimeError(
                    f"Failed to download image: {resp.status_code}, url: {file}"
                )
            file = resp.content
            if not isinstance(file, bytes):
                raise TypeError(f"Unsupported type of file: {type(file)}, need bytes")

        upload_result = await bot.set_resouce_picture_upload(
            file=file, file_name=image.data["name"] + ".png"  # 上传是文件名必须携带有效后缀
        )
        logger.debug(f"Uploaded result: {upload_result}")
        return MessageSegment.picture(**upload_result.dict())

    @register_dodo(Reply)
    def _reply(reply: Reply) -> MessageSegment:
        assert isinstance(reply.data, DodoMessageId)
        return MessageSegment.reference(reply.data.message_id)

    @register_dodo(Mention)
    def _mention(mention: Mention) -> MessageSegment:
        return MessageSegment.at_user(dodo_id=mention.data["user_id"])

    @register_target_extractor(ChannelMessageEvent)
    def _extract_channel_msg_event(event: Event) -> TargetDoDoChannel:
        assert isinstance(event, ChannelMessageEvent)
        return TargetDoDoChannel(channel_id=event.channel_id)

    @register_target_extractor(GiftSendEvent)
    @register_target_extractor(ChannelArticleEvent)
    @register_target_extractor(MessageReactionEvent)
    @register_target_extractor(CardMessageFormSubmitEvent)
    @register_target_extractor(CardMessageListSubmitEvent)
    @register_target_extractor(ChannelArticleCommentEvent)
    @register_target_extractor(CardMessageButtonClickEvent)
    @register_target_extractor(ChannelVoiceMemberJoinEvent)
    @register_target_extractor(ChannelVoiceMemberLeaveEvent)
    def _extract_notice_event(event: Event) -> TargetDoDoChannel:
        assert isinstance(
            event,
            (
                GiftSendEvent,
                ChannelArticleEvent,
                MessageReactionEvent,
                CardMessageFormSubmitEvent,
                CardMessageListSubmitEvent,
                ChannelArticleCommentEvent,
                CardMessageButtonClickEvent,
                ChannelVoiceMemberJoinEvent,
                ChannelVoiceMemberLeaveEvent,
            ),
        )
        return TargetDoDoChannel(channel_id=event.channel_id)

    @register_target_extractor(PersonalMessageEvent)
    def _extract_personal_msg_event(event: Event) -> TargetDoDoPrivate:
        assert isinstance(event, PersonalMessageEvent)
        island_source_id = event.island_source_id
        if island_source_id is None:
            raise ValueError("island_source_id is None")
        return TargetDoDoPrivate(
            dodo_source_id=event.dodo_source_id, island_source_id=island_source_id
        )

    @register_convert_to_arg(adapter, SupportedPlatform.dodo_channel)
    def _gen_channel(target: PlatformTarget) -> Dict[str, Any]:
        assert isinstance(target, TargetDoDoChannel)
        args = {
            "channel_id": target.channel_id,
        }
        if target.dodo_source_id:
            args["dodo_source_id"] = target.dodo_source_id
        return args

    @register_convert_to_arg(adapter, SupportedPlatform.dodo_private)
    def _gen_private(target: PlatformTarget) -> Dict[str, Any]:
        assert isinstance(target, TargetDoDoPrivate)
        return {
            "dodo_source_id": target.dodo_source_id,
            "island_source_id": target.island_source_id,
        }

    class DodoReceipt(Receipt):
        adapter_name: Literal[adapter] = adapter
        message_id: str

        async def revoke(self, reason: Optional[str] = None):
            return await cast(BotDodo, self._get_bot()).set_channel_message_withdraw(
                message_id=self.message_id, reason=reason
            )

        async def edit(self, mesaage_body: MessageBody):
            return await cast(BotDodo, self._get_bot()).set_channel_message_edit(
                message_id=self.message_id, message_body=mesaage_body
            )

        async def pin(self, is_cancel: bool = False):
            """置顶消息"""
            return await cast(BotDodo, self._get_bot()).set_channel_message_top(
                message_id=self.message_id, is_cancel=is_cancel
            )

        @property
        def raw(self) -> str:
            return self.message_id

    @register_sender(adapter)
    async def send(
        bot,
        msg: MessageFactory[MessageSegmentFactory],
        target,
        event,
        at_sender: bool,
        reply: bool,
    ) -> DodoReceipt:
        assert isinstance(bot, BotDodo)
        assert isinstance(target, (TargetDoDoChannel, TargetDoDoPrivate))

        if event:
            assert isinstance(event, MessageEvent)
            full_msg = assamble_message_factory(
                msg,
                Mention(event.get_user_id()),
                Reply(DodoMessageId(message_id=event.message_id)),
                at_sender,
                reply,
            )
        else:
            full_msg = msg

        message_to_send = Message()
        for segment_factory in full_msg:
            message_segment = await segment_factory.build(bot)
            message_to_send += message_segment

        if isinstance(target, TargetDoDoChannel):
            if target.dodo_source_id:
                resp = await bot.send_to_channel_personal(
                    message=message_to_send, **target.arg_dict(bot)
                )
            else:
                resp = await bot.send_to_channel(
                    message=message_to_send, **target.arg_dict(bot)
                )
        else:
            resp = await bot.send_to_personal(
                message=message_to_send, **target.arg_dict(bot)
            )

        return DodoReceipt(message_id=resp, bot_id=bot.self_id)

    @register_list_targets(adapter)
    async def list_targets(bot: BaseBot) -> List[PlatformTarget]:
        assert isinstance(bot, BotDodo)
        targets = []
        for island in await bot.get_island_list():
            for channel in await bot.get_channel_list(
                island_source_id=island.island_source_id
            ):
                targets.append(TargetDoDoChannel(channel_id=channel.channel_id))

        # TODO: 私聊

        return targets
