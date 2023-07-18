from functools import partial
from typing import Any, Dict, List, Union, Optional

from nonebot.adapters import Bot, Event

from ..types import Text, Image, Reply, Mention
from ..utils import (
    TargetQQGroup,
    MessageFactory,
    PlatformTarget,
    TargetQQPrivate,
    SupportedAdapters,
    SupportedPlatform,
    MessageSegmentFactory,
    AggregatedMessageFactory,
    register_sender,
    register_ms_adapter,
    register_list_targets,
    register_convert_to_arg,
    assamble_message_factory,
    register_target_extractor,
)

try:
    from nonebot.adapters.onebot.v11 import Bot as BotOB11
    from nonebot.adapters.onebot.v11.message import Message, MessageSegment
    from nonebot.adapters.onebot.v11 import (
        NotifyEvent,
        MessageEvent,
        GroupMessageEvent,
        PrivateMessageEvent,
    )

    adapter = SupportedAdapters.onebot_v11
    register_onebot_v11 = partial(register_ms_adapter, adapter)

    MessageFactory.register_adapter_message(SupportedAdapters.onebot_v11, Message)

    @register_onebot_v11(Text)
    def _text(t: Text) -> MessageSegment:
        return MessageSegment.text(t.data["text"])

    @register_onebot_v11(Image)
    async def _image(i: Image) -> MessageSegment:
        return MessageSegment.image(i.data["image"])

    @register_onebot_v11(Mention)
    async def _mention(m: Mention) -> MessageSegment:
        return MessageSegment.at(m.data["user_id"])

    @register_onebot_v11(Reply)
    async def _reply(r: Reply) -> MessageSegment:
        return MessageSegment.reply(int(r.data["message_id"]))

    @register_target_extractor(PrivateMessageEvent)
    def _extract_private_msg_event(event: Event) -> TargetQQPrivate:
        assert isinstance(event, PrivateMessageEvent)
        return TargetQQPrivate(user_id=event.user_id)

    @register_target_extractor(GroupMessageEvent)
    def _extract_group_msg_event(event: Event) -> TargetQQGroup:
        assert isinstance(event, GroupMessageEvent)
        return TargetQQGroup(group_id=event.group_id)

    @register_target_extractor(NotifyEvent)
    def _extract_notify_event(event: Event) -> Union[TargetQQPrivate, TargetQQGroup]:
        assert isinstance(event, NotifyEvent)
        if event.group_id:
            return TargetQQGroup(group_id=event.group_id)
        else:
            return TargetQQPrivate(user_id=event.user_id)

    @register_convert_to_arg(adapter, SupportedPlatform.qq_private)
    def _gen_private(target: PlatformTarget) -> Dict[str, Any]:
        assert isinstance(target, TargetQQPrivate)
        return {
            "message_type": "private",
            "user_id": target.user_id,
        }

    @register_convert_to_arg(adapter, SupportedPlatform.qq_group)
    def _gen_group(target: PlatformTarget) -> Dict[str, Any]:
        assert isinstance(target, TargetQQGroup)
        return {
            "message_type": "group",
            "group_id": target.group_id,
        }

    @register_sender(SupportedAdapters.onebot_v11)
    async def send(
        bot,
        msg: MessageFactory[MessageSegmentFactory],
        target,
        event,
        at_sender: bool,
        reply: bool,
    ):
        assert isinstance(bot, BotOB11)
        assert isinstance(target, (TargetQQGroup, TargetQQPrivate))
        if event:
            assert isinstance(event, MessageEvent)
            full_msg = assamble_message_factory(
                msg,
                Mention(event.get_user_id()),
                Reply(event.message_id),
                at_sender,
                reply,
            )
        else:
            full_msg = msg
        message_to_send = Message()
        for message_segment_factory in full_msg:
            message_segment = await message_segment_factory.build(bot)
            message_to_send += message_segment
        await bot.send_msg(message=message_to_send, **target.arg_dict(bot))

    @AggregatedMessageFactory.register_aggregated_sender(adapter)
    async def aggregate_send(
        bot: Bot,
        message_factories: List[MessageFactory],
        target: PlatformTarget,
        event: Optional[Event],
    ):
        assert isinstance(bot, BotOB11)
        login_info = await bot.get_login_info()

        msg_list: List[Message] = []
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
    async def list_targets(bot: Bot) -> List[PlatformTarget]:
        assert isinstance(bot, BotOB11)

        targets = []
        groups = await bot.get_group_list()
        for group in groups:
            group_id = group["group_id"]
            target = TargetQQGroup(group_id=group_id)
            targets.append(target)

        # 获取好友列表
        users = await bot.get_friend_list()
        for user in users:
            user_id = user["user_id"]
            target = TargetQQPrivate(user_id=user_id)
            targets.append(target)

        return targets

except ImportError:
    pass
except Exception as e:
    raise e
