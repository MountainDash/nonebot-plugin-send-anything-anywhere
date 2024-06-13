from io import BytesIO
from pathlib import Path
from datetime import datetime
from functools import partial
from contextlib import suppress
from collections.abc import Awaitable
from typing import Any, Generic, Literal, TypeVar, Optional, Protocol, cast

from yarl import URL
from nonebot import logger
from nonebot.adapters import Event
from nonebot.adapters import Bot as BaseBot
from nonebot.compat import model_dump, type_validate_python

from ..auto_select_bot import register_list_targets
from ..types import Text, Image, Reply, Mention, MentionAll
from ..utils import SupportedAdapters, SupportedPlatform, type_message_id_check
from ..abstract_factories import (
    MessageFactory,
    AggregatedMessageFactory,
    register_ms_adapter,
    assamble_message_factory,
)
from ..registries import (
    Receipt,
    MessageId,
    TargetQQGroup,
    PlatformTarget,
    TargetQQPrivate,
    TargetKritorUnknown,
    TargetQQGuildChannel,
    register_sender,
    register_convert_to_arg,
    register_target_extractor,
    register_message_id_getter,
)

with suppress(ImportError):
    from nonebot.adapters.kritor import Bot as BotKritor
    from nonebot.adapters.kritor.message import Message, MessageSegment
    from nonebot.adapters.kritor.model import Group, Guild, Friend, Contact, SceneType
    from nonebot.adapters.kritor.protos.kritor.common import (
        Sender,
        PushMessageBody,
        ForwardMessageBody,
    )
    from nonebot.adapters.kritor.event import (
        MessageEvent,
        GroupPokeNotice,
        GroupApplyRequest,
        GroupRecallNotice,
        GroupSignInNotice,
        PrivatePokeNotice,
        FriendApplyRequest,
        GroupWholeBanNotice,
        PrivateRecallNotice,
        GroupMemberBanNotice,
        GroupCardChangedNotice,
        GroupAdminChangedNotice,
        GroupFileUploadedNotice,
        InvitedJoinGroupRequest,
        GroupEssenceMessageNotice,
        PrivateFileUploadedNotice,
        GroupMemberDecreasedNotice,
        GroupMemberIncreasedNotice,
        GroupUniqueTitleChangedNotice,
        GroupReactMessageWithEmojiNotice,
    )

    TGetList = TypeVar("TGetList")

    adapter = SupportedAdapters.kritor
    register_kritor = partial(register_ms_adapter, adapter)

    class KritorMessageId(MessageId):
        adapter_name: Literal[adapter] = adapter

        message_id: str

    MessageFactory.register_adapter_message(SupportedAdapters.kritor, Message)

    @register_message_id_getter(MessageEvent)
    def _get_message_id(event: Event) -> KritorMessageId:
        assert isinstance(event, MessageEvent)
        return KritorMessageId(message_id=event.message_id)

    @register_kritor(Text)
    async def _text(t: Text) -> MessageSegment:
        return MessageSegment.text(t.data["text"])

    @register_kritor(Image)
    async def _image(i: Image) -> MessageSegment:
        file = i.data["image"]
        if isinstance(file, str):
            if (uri := URL(file)).is_absolute() and uri.scheme in ("http", "https"):
                return MessageSegment.image(url=file)
            elif path := Path(file):
                return MessageSegment.image(path=path)
            else:
                raise TypeError(f"Invalid image str value: {file}")
        elif isinstance(file, Path):
            return MessageSegment.image(path=file)
        elif isinstance(file, (bytes, BytesIO)):
            return MessageSegment.image(raw=file)
        else:
            raise TypeError(f"Unsupported type of image: {type(file)}")

    @register_kritor(Reply)
    async def _reply(r: Reply) -> MessageSegment:
        mid = type_message_id_check(KritorMessageId, r.data["message_id"])
        return MessageSegment.reply(message_id=mid.message_id)

    @register_kritor(Mention)
    async def _mention(m: Mention) -> MessageSegment:
        return MessageSegment.at(uid=m.data["user_id"])

    @register_kritor(MentionAll)
    async def _mention_all(m: MentionAll) -> MessageSegment:
        return MessageSegment.atall()

    @register_target_extractor(MessageEvent)
    def _extract_target(event: Event) -> PlatformTarget:
        assert isinstance(event, MessageEvent)
        uid = event.get_user_id()
        contact = event.contact
        if contact.type == SceneType.GROUP:
            return TargetQQGroup(group_id=int(uid))
        elif contact.type == SceneType.FRIEND:
            return TargetQQPrivate(user_id=int(uid))
        elif contact.type == SceneType.GUILD:
            channel_id = event.contact.sub_id
            assert channel_id, "Guild channel id is required"
            return TargetQQGuildChannel(guild_id=uid, channel_id=int(channel_id))
        else:
            logger.warning(f"Message Contact type maybe not sendable: {contact}")
            return TargetKritorUnknown(
                primary_id=uid, secondary_id=contact.sub_id, type=str(contact.type)
            )

    @register_target_extractor(FriendApplyRequest)
    @register_target_extractor(PrivatePokeNotice)
    @register_target_extractor(PrivateRecallNotice)
    @register_target_extractor(PrivateFileUploadedNotice)
    def _extract_friend_apply_request(event: Event) -> PlatformTarget:
        assert isinstance(event, FriendApplyRequest)
        return TargetQQPrivate(user_id=int(event.get_user_id()))

    @register_target_extractor(GroupApplyRequest)
    @register_target_extractor(InvitedJoinGroupRequest)
    @register_target_extractor(GroupUniqueTitleChangedNotice)
    @register_target_extractor(GroupEssenceMessageNotice)
    @register_target_extractor(GroupPokeNotice)
    @register_target_extractor(GroupCardChangedNotice)
    @register_target_extractor(GroupMemberIncreasedNotice)
    @register_target_extractor(GroupMemberDecreasedNotice)
    @register_target_extractor(GroupAdminChangedNotice)
    @register_target_extractor(GroupMemberBanNotice)
    @register_target_extractor(GroupRecallNotice)
    @register_target_extractor(GroupSignInNotice)
    @register_target_extractor(GroupWholeBanNotice)
    @register_target_extractor(GroupReactMessageWithEmojiNotice)
    @register_target_extractor(GroupFileUploadedNotice)
    def _extract_group_apply_request(event: Event) -> PlatformTarget:
        assert isinstance(
            event,
            (
                GroupApplyRequest,
                InvitedJoinGroupRequest,
                GroupUniqueTitleChangedNotice,
                GroupEssenceMessageNotice,
                GroupPokeNotice,
                GroupCardChangedNotice,
                GroupMemberIncreasedNotice,
                GroupMemberDecreasedNotice,
                GroupAdminChangedNotice,
                GroupMemberBanNotice,
                GroupRecallNotice,
                GroupSignInNotice,
                GroupWholeBanNotice,
                GroupReactMessageWithEmojiNotice,
                GroupFileUploadedNotice,
            ),
        )
        return TargetQQGroup(group_id=int(event.get_user_id()))

    @register_convert_to_arg(adapter, SupportedPlatform.qq_private)
    def _gen_private(target: PlatformTarget) -> dict[str, Any]:
        assert isinstance(target, TargetQQPrivate)
        return model_dump(Friend(peer=str(target.user_id), sub_peer=None))

    @register_convert_to_arg(adapter, SupportedPlatform.qq_group)
    def _gen_group(target: PlatformTarget) -> dict[str, Any]:
        assert isinstance(target, TargetQQGroup)
        return model_dump(Group(peer=str(target.group_id), sub_peer=None))

    @register_convert_to_arg(adapter, SupportedPlatform.qq_guild_channel)
    def _gen_guild_channel(target: PlatformTarget) -> dict[str, Any]:
        assert isinstance(target, TargetQQGuildChannel)
        return model_dump(
            Guild(peer=str(target.guild_id), sub_peer=str(target.channel_id))
        )

    @register_convert_to_arg(adapter, SupportedPlatform.kritor_unknown)
    def _gen_stranger_group(target: PlatformTarget) -> dict[str, Any]:
        assert isinstance(target, TargetKritorUnknown)
        return model_dump(
            type_validate_python(
                Contact,
                {
                    "peer": str(target.primary_id),
                    "sub_peer": str(target.secondary_id or 0),
                    "scene": SceneType(str(target.type)),
                },
            )
        )

    class KritorReceipt(Receipt):
        adapter_name: Literal[adapter] = adapter
        message_id: str
        origin_contact: Contact

        async def revoke(self):
            return await cast(BotKritor, self._get_bot()).recall_message(
                message_id=self.message_id
            )

        async def essence(self):
            """消息加精"""
            return await cast(BotKritor, self._get_bot()).set_essence_message(
                group_id=self.origin_contact, message_id=self.message_id
            )

        async def unessence(self):
            """取消消息加精"""
            return await cast(BotKritor, self._get_bot()).delete_essence_message(
                group_id=self.origin_contact, message_id=self.message_id
            )

        async def get_message(self):
            """获取完整消息"""
            return await cast(BotKritor, self._get_bot()).get_message(
                message_id=self.message_id
            )

        async def react(self, emoji: int, is_set: bool = True):
            """设置消息评论表情"""
            return await cast(BotKritor, self._get_bot()).set_message_comment_emoji(
                contact=self.origin_contact,
                message_id=self.message_id,
                emoji=emoji,
                is_set=is_set,
            )

        @property
        def raw(self) -> str:
            return self.message_id

        def extract_message_id(self) -> KritorMessageId:
            return KritorMessageId(message_id=self.message_id)

    @register_sender(adapter)
    async def send(
        bot,
        msg: MessageFactory,
        target,
        event,
        at_sender: bool,
        reply: bool,
    ) -> KritorReceipt:
        assert isinstance(bot, BotKritor)
        assert isinstance(
            target,
            (
                TargetQQGroup,
                TargetQQPrivate,
                TargetQQGuildChannel,
            ),
        )

        if event:
            assert isinstance(event, MessageEvent)
            contact = event.contact
            full_msg = assamble_message_factory(
                msg,
                Mention(event.get_user_id()),
                Reply(KritorMessageId(message_id=event.message_id)),
                at_sender,
                reply,
            )
            message_id = event.message_id
        else:
            contact = type_validate_python(Contact, target.arg_dict(bot))
            full_msg = msg
            message_id = None

        message_to_send = Message()
        for segment_factory in full_msg:
            message_segment = await segment_factory.build(bot)
            message_to_send += message_segment

        if contact.type != SceneType.GUILD:
            resp = await bot.send_message(
                contact=contact,
                elements=message_to_send.to_elements(),
                message_id=message_id,
            )

            return KritorReceipt(
                message_id=resp.message_id,
                origin_contact=contact,
                bot_id=bot.self_id,
            )
        else:
            resp = await bot.send_channel_message(
                guild_id=int(contact.id),
                channel_id=int(contact.sub_id or 0),
                message=str(message_to_send),
            )

            return KritorReceipt(
                message_id=resp.message_id,
                origin_contact=contact,
                bot_id=bot.self_id,
            )

    @AggregatedMessageFactory.register_aggregated_sender(adapter)
    async def aggregate_send(
        bot: BaseBot,
        message_factories: list[MessageFactory],
        target: PlatformTarget,
        event: Optional[Event],
    ):
        assert isinstance(bot, BotKritor)
        bot_info = await bot.get_bot_info()

        forward_msg_list: list[ForwardMessageBody] = []
        for msg_fac in message_factories:
            msg = await msg_fac.build(bot)
            assert isinstance(msg, Message)
            forward_msg_list.append(
                ForwardMessageBody(
                    message=PushMessageBody(
                        time=int(datetime.now().timestamp()),
                        sender=Sender(
                            uid=bot.self_id,
                            uin=int(bot.self_id),
                            nick=bot_info.nickname,
                        ),
                    )
                )
            )

        if event:
            assert isinstance(event, MessageEvent)
            contact = event.contact
        else:
            contact = type_validate_python(Contact, target.arg_dict(bot))

        await bot.send_forward_message(
            contact=contact,
            messages=forward_msg_list,
        )

    class GetListAPI(Generic[TGetList], Protocol):
        def __call__(self) -> Awaitable[list[TGetList]]: ...

    async def _get_list_or_warn(get_list_api: GetListAPI[TGetList]) -> list[TGetList]:
        try:
            return await get_list_api()
        except Exception:
            logger.exception(f"Error when api {get_list_api.__qualname__} get list")
            return []

    @register_list_targets(adapter)
    async def list_targets(bot: BaseBot) -> list[PlatformTarget]:
        assert isinstance(bot, BotKritor)
        targets: list[PlatformTarget] = []

        for friend in await _get_list_or_warn(bot.get_friend_list):
            targets.append(TargetQQPrivate(user_id=int(friend.uid)))

        for group in await _get_list_or_warn(bot.get_group_list):
            targets.append(TargetQQGroup(group_id=int(group.group_id)))

        for guild in await _get_list_or_warn(bot.get_guild_list):
            guild_id = guild.guild_id
            for channel in await _get_list_or_warn(
                partial(bot.get_guild_channel_list, guild_id=guild_id)
            ):
                targets.append(
                    TargetQQGuildChannel(
                        guild_id=str(guild_id), channel_id=channel.channel_id
                    )
                )

        return targets
