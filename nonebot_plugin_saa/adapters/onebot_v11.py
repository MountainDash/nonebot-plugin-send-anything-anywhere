from functools import partial
from typing import Any, Union, Literal, Optional, cast

from nonebot.adapters import Bot, Event
from nonebot.adapters.onebot.v11 import Bot as BotOB11
from nonebot.adapters.onebot.v11.message import Message, MessageSegment
from nonebot.adapters.onebot.v11 import (
    MessageEvent,
    PokeNotifyEvent,
    HonorNotifyEvent,
    GroupMessageEvent,
    GroupRequestEvent,
    FriendRequestEvent,
    GroupBanNoticeEvent,
    PrivateMessageEvent,
    FriendAddNoticeEvent,
    LuckyKingNotifyEvent,
    GroupAdminNoticeEvent,
    GroupRecallNoticeEvent,
    GroupUploadNoticeEvent,
    FriendRecallNoticeEvent,
    GroupDecreaseNoticeEvent,
    GroupIncreaseNoticeEvent,
)

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
    register_sender,
    register_convert_to_arg,
    register_target_extractor,
    register_message_id_getter,
)

adapter = SupportedAdapters.onebot_v11
register_onebot_v11 = partial(register_ms_adapter, adapter)

MessageFactory.register_adapter_message(SupportedAdapters.onebot_v11, Message)


class OB11MessageId(MessageId):
    adapter_name: Literal[SupportedAdapters.onebot_v11] = adapter

    message_id: int


@register_onebot_v11(Text)
def _text(t: Text) -> MessageSegment:
    return MessageSegment.text(t.data["text"])


@register_onebot_v11(Image)
async def _image(i: Image) -> MessageSegment:
    return MessageSegment.image(i.data["image"])


@register_onebot_v11(Mention)
async def _mention(m: Mention) -> MessageSegment:
    return MessageSegment.at(m.data["user_id"])


@register_onebot_v11(MentionAll)
async def _mention_all(m: MentionAll) -> MessageSegment:
    return MessageSegment.at("all")


@register_onebot_v11(Reply)
async def _reply(r: Reply) -> MessageSegment:
    mid = type_message_id_check(OB11MessageId, r.data["message_id"])
    return MessageSegment.reply(mid.message_id)


@register_target_extractor(PrivateMessageEvent)
def _extract_private_msg_event(event: Event) -> TargetQQPrivate:
    assert isinstance(event, PrivateMessageEvent)
    return TargetQQPrivate(user_id=event.user_id)


@register_target_extractor(GroupMessageEvent)
def _extract_group_msg_event(event: Event) -> TargetQQGroup:
    assert isinstance(event, GroupMessageEvent)
    return TargetQQGroup(group_id=event.group_id)


@register_target_extractor(FriendAddNoticeEvent)
@register_target_extractor(FriendRecallNoticeEvent)
def _extract_friend_notice_event(event: Event) -> TargetQQPrivate:
    assert isinstance(event, (FriendAddNoticeEvent, FriendRecallNoticeEvent))
    return TargetQQPrivate(user_id=event.user_id)


@register_target_extractor(GroupBanNoticeEvent)
@register_target_extractor(GroupAdminNoticeEvent)
@register_target_extractor(GroupRecallNoticeEvent)
@register_target_extractor(GroupUploadNoticeEvent)
@register_target_extractor(GroupDecreaseNoticeEvent)
@register_target_extractor(GroupIncreaseNoticeEvent)
def _extract_group_notice_event(event: Event) -> TargetQQGroup:
    assert isinstance(
        event,
        (
            GroupBanNoticeEvent,
            GroupAdminNoticeEvent,
            GroupRecallNoticeEvent,
            GroupUploadNoticeEvent,
            GroupDecreaseNoticeEvent,
            GroupIncreaseNoticeEvent,
        ),
    )
    return TargetQQGroup(group_id=event.group_id)


@register_target_extractor(HonorNotifyEvent)
@register_target_extractor(LuckyKingNotifyEvent)
def _extract_group_notify_event(event: Event) -> TargetQQGroup:
    assert isinstance(event, (HonorNotifyEvent, LuckyKingNotifyEvent))
    return TargetQQGroup(group_id=event.group_id)


@register_target_extractor(FriendRequestEvent)
def _extract_friend_request_event(event: Event) -> TargetQQPrivate:
    assert isinstance(event, FriendRequestEvent)
    return TargetQQPrivate(user_id=event.user_id)


@register_target_extractor(GroupRequestEvent)
def _extract_group_request_event(event: Event) -> TargetQQGroup:
    assert isinstance(event, GroupRequestEvent)
    return TargetQQGroup(group_id=event.group_id)


@register_target_extractor(PokeNotifyEvent)
def _extract_poke_notify_event(
    event: Event,
) -> Union[TargetQQPrivate, TargetQQGroup]:
    assert isinstance(event, PokeNotifyEvent)
    if event.group_id is not None:
        return TargetQQGroup(group_id=event.group_id)
    else:
        return TargetQQPrivate(user_id=event.user_id)


@register_message_id_getter(MessageEvent)
def _(event: Event) -> OB11MessageId:
    assert isinstance(event, MessageEvent)
    return OB11MessageId(message_id=event.message_id)


@register_convert_to_arg(adapter, SupportedPlatform.qq_private)
def _gen_private(target: PlatformTarget) -> dict[str, Any]:
    assert isinstance(target, TargetQQPrivate)
    return {
        "message_type": "private",
        "user_id": target.user_id,
    }


@register_convert_to_arg(adapter, SupportedPlatform.qq_group)
def _gen_group(target: PlatformTarget) -> dict[str, Any]:
    assert isinstance(target, TargetQQGroup)
    return {
        "message_type": "group",
        "group_id": target.group_id,
    }


class OB11Receipt(Receipt):
    message_id: int
    adapter_name: Literal[SupportedAdapters.onebot_v11] = adapter

    async def revoke(self):
        return await cast(BotOB11, self._get_bot()).delete_msg(
            message_id=self.message_id
        )

    @property
    def raw(self) -> Any:
        return self.message_id

    def extract_message_id(self) -> OB11MessageId:
        return OB11MessageId(message_id=self.message_id)


@register_sender(SupportedAdapters.onebot_v11)
async def send(
    bot,
    msg: MessageFactory,
    target,
    event,
    at_sender: bool,
    reply: bool,
) -> OB11Receipt:
    assert isinstance(bot, BotOB11)
    assert isinstance(target, (TargetQQGroup, TargetQQPrivate))
    if event:
        assert isinstance(event, MessageEvent)
        full_msg = assamble_message_factory(
            msg,
            Mention(event.get_user_id()),
            Reply(OB11MessageId(message_id=event.message_id)),
            at_sender,
            reply,
        )
    else:
        full_msg = msg
    message_to_send = Message()
    for message_segment_factory in full_msg:
        message_segment = await message_segment_factory.build(bot)
        message_to_send += message_segment
    # https://github.com/botuniverse/onebot-11/blob/master/api/public.md#send_msg-%E5%8F%91%E9%80%81%E6%B6%88%E6%81%AF
    res_dict = await bot.send_msg(message=message_to_send, **target.arg_dict(bot))
    message_id = cast(int, res_dict["message_id"])
    return OB11Receipt(bot_id=bot.self_id, message_id=message_id)


@AggregatedMessageFactory.register_aggregated_sender(adapter)
async def aggregate_send(
    bot: Bot,
    message_factories: list[MessageFactory],
    target: PlatformTarget,
    event: Optional[Event],
):
    assert isinstance(bot, BotOB11)
    login_info = await bot.get_login_info()

    msg_list: list[Message] = []
    for msg_fac in message_factories:
        msg = await msg_fac.build(bot)
        assert isinstance(msg, Message)
        msg_list.append(msg)
    aggregated_message_segment = Message(
        [
            MessageSegment.node_custom(
                user_id=login_info["user_id"],
                nickname=login_info["nickname"],
                content=msg,
            )
            for msg in msg_list
        ]
    )

    if isinstance(target, TargetQQGroup):
        await bot.send_group_forward_msg(
            group_id=target.group_id, messages=aggregated_message_segment
        )
    elif isinstance(target, TargetQQPrivate):
        await bot.send_private_forward_msg(
            user_id=target.user_id, messages=aggregated_message_segment
        )
    else:  # pragma: no cover
        raise RuntimeError(f"{target.__class__.__name__} not supported")


@register_list_targets(SupportedAdapters.onebot_v11)
async def list_targets(bot: Bot) -> list[PlatformTarget]:
    assert isinstance(bot, BotOB11)

    targets = []
    try:
        groups = await bot.get_group_list()
    except Exception:
        groups = []

    for group in groups:
        group_id = group["group_id"]
        target = TargetQQGroup(group_id=group_id)
        targets.append(target)

    # 获取好友列表
    try:
        users = await bot.get_friend_list()
    except Exception:
        users = []

    for user in users:
        user_id = user["user_id"]
        target = TargetQQPrivate(user_id=user_id)
        targets.append(target)

    return targets
