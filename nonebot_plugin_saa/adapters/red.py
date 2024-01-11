from datetime import datetime
from functools import partial
from typing import Any, Dict, List, Literal, Optional, cast

from nonebot import get_driver
from nonebot.adapters import Bot, Event
from nonebot.drivers import Request, HTTPClientMixin

from ..types import Text, Image, Reply, Mention
from ..auto_select_bot import register_list_targets
from ..utils import SupportedAdapters, SupportedPlatform
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
)

try:
    from nonebot.adapters.red import Bot as BotRed
    from nonebot.adapters.red.api.model import ChatType
    from nonebot.adapters.red.message import ForwardNode
    from nonebot.adapters.red.api.model import Message as MessageModel
    from nonebot.adapters.red import (
        Message,
        MessageEvent,
        MessageSegment,
        GroupMessageEvent,
        PrivateMessageEvent,
    )

    adapter = SupportedAdapters.red
    register_red = partial(register_ms_adapter, adapter)

    MessageFactory.register_adapter_message(SupportedAdapters.red, Message)

    class RedMessageId(MessageId):
        adapter_name: Literal[adapter] = adapter
        message_seq: str
        message_id: Optional[str] = None
        sender_uin: Optional[str] = None

    @register_red(Text)
    def _text(t: Text) -> MessageSegment:
        return MessageSegment.text(t.data["text"])

    @register_red(Image)
    async def _image(i: Image) -> MessageSegment:
        image = i.data["image"]
        if isinstance(image, str):
            driver = get_driver()
            assert isinstance(driver, HTTPClientMixin), "driver should be ForwardDriver"
            image_data = await driver.request(Request("GET", image))
            assert isinstance(image_data.content, bytes)
            return MessageSegment.image(image_data.content)
        return MessageSegment.image(image)

    @register_red(Mention)
    async def _mention(m: Mention) -> MessageSegment:
        return MessageSegment.at(m.data["user_id"])

    @register_red(Reply)
    async def _reply(r: Reply) -> MessageSegment:
        assert isinstance(mid := r.data["message_id"], RedMessageId)
        return MessageSegment.reply(
            message_seq=mid.message_seq,
            message_id=mid.message_id,
            sender_uin=mid.sender_uin,
        )

    @register_target_extractor(PrivateMessageEvent)
    def _extract_private_msg_event(event: Event) -> TargetQQPrivate:
        assert isinstance(event, PrivateMessageEvent)
        assert event.senderUin, "senderUin should not be None for private message"
        return TargetQQPrivate(user_id=int(event.senderUin))

    @register_target_extractor(GroupMessageEvent)
    def _extract_group_msg_event(event: Event) -> TargetQQGroup:
        assert isinstance(event, GroupMessageEvent)
        assert event.peerUin, "peerUin should not be None for group message"
        return TargetQQGroup(group_id=int(event.peerUin))

    @register_convert_to_arg(adapter, SupportedPlatform.qq_private)
    def _gen_private(target: PlatformTarget) -> Dict[str, Any]:
        assert isinstance(target, TargetQQPrivate)
        return {
            "chat_type": ChatType.FRIEND,
            "target": str(target.user_id),
        }

    @register_convert_to_arg(adapter, SupportedPlatform.qq_group)
    def _gen_group(target: PlatformTarget) -> Dict[str, Any]:
        assert isinstance(target, TargetQQGroup)
        return {
            "chat_type": ChatType.GROUP,
            "target": str(target.group_id),
        }

    class RedReceipt(Receipt):
        adapter_name: Literal[adapter] = adapter
        message: MessageModel

        async def revoke(self):
            assert self.message.peerUin, "peerUin should not be None"
            return await cast(BotRed, self._get_bot()).recall_message(
                self.message.chatType,
                self.message.peerUin,
                self.message.msgId,
            )

        @property
        def raw(self) -> MessageModel:
            return self.message

    @register_sender(SupportedAdapters.red)
    async def send(
        bot,
        msg: MessageFactory,
        target,
        event,
        at_sender: bool,
        reply: bool,
    ) -> RedReceipt:
        assert isinstance(bot, BotRed)
        assert isinstance(target, (TargetQQGroup, TargetQQPrivate))
        if event:
            assert isinstance(event, MessageEvent)
            full_msg = assamble_message_factory(
                msg,
                Mention(event.get_user_id()),
                Reply(
                    RedMessageId(
                        message_seq=event.msgSeq,
                        message_id=event.msgId,
                        sender_uin=event.senderUin,
                    )
                ),
                at_sender,
                reply,
            )
        else:
            full_msg = msg
        message_to_send = Message()
        for message_segment_factory in full_msg:
            message_segment = await message_segment_factory.build(bot)
            message_to_send += message_segment
        resp = await bot.send_message(message=message_to_send, **target.arg_dict(bot))

        return RedReceipt(bot_id=bot.self_id, message=resp)

    @AggregatedMessageFactory.register_aggregated_sender(adapter)
    async def aggregate_send(
        bot: Bot,
        message_factories: List[MessageFactory],
        target: PlatformTarget,
        event: Optional[Event],
    ):
        assert isinstance(bot, BotRed)

        msg_list: List[Message] = []
        for msg_fac in message_factories:
            msg = await msg_fac.build(bot)
            assert isinstance(msg, Message)
            msg_list.append(msg)
        nodes = [
            ForwardNode(
                uin=bot.self_id,
                name=bot.self_id,
                group=bot.self_id,
                message=msg,
                time=datetime.now(),
            )
            for msg in msg_list
        ]
        if isinstance(target, TargetQQGroup):
            await bot.send_fake_forward(
                nodes=nodes, chat_type=ChatType.GROUP, target=target.group_id
            )
        elif isinstance(target, TargetQQPrivate):
            await bot.send_fake_forward(
                nodes=nodes, chat_type=ChatType.FRIEND, target=target.user_id
            )
        else:  # pragma: no cover
            raise RuntimeError(f"{target.__class__.__name__} not supported")

    @register_list_targets(SupportedAdapters.red)
    async def list_targets(bot: Bot) -> List[PlatformTarget]:
        assert isinstance(bot, BotRed)

        targets = []
        try:
            groups = await bot.get_groups()
        except Exception:
            groups = []
        for group in groups:
            group_id = int(group.groupCode)
            target = TargetQQGroup(group_id=group_id)
            targets.append(target)

        # 获取好友列表
        try:
            users = await bot.get_friends()
        except Exception:
            users = []
        for user in users:
            user_id = int(user.uin)
            target = TargetQQPrivate(user_id=user_id)
            targets.append(target)

        return targets

except ImportError:
    pass
except Exception as e:
    raise e
