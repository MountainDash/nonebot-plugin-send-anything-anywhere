from enum import Enum
from io import BytesIO
from pathlib import Path
from functools import partial
from typing import (
    Any,
    Dict,
    List,
    Generic,
    Literal,
    TypeVar,
    Optional,
    Protocol,
    Awaitable,
    cast,
)

from nonebot import logger
from filetype import guess_mime
from nonebot.adapters import Bot, Event

from ..auto_select_bot import register_list_targets
from ..utils import SupportedAdapters, SupportedPlatform
from ..types import Text, Image, Reply, Mention, MentionAll
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
    TargetFeishuGroup,
    TargetFeishuPrivate,
    TargetSatoriUnknown,
    TargetTelegramCommon,
    TargetKaiheilaChannel,
    TargetKaiheilaPrivate,
    register_sender,
    register_convert_to_arg,
    register_target_extractor,
)


class SatoriPlatform(str, Enum):
    QQ = "qq"
    RED = "red"
    CHRONOCAT = "chronocat"
    KOOK = "kook"
    TELEGRAM = "telegram"
    FEISHU = "feishu"


try:
    from nonebot.exception import ActionFailed
    from nonebot.adapters.satori import Bot as BotSatori
    from nonebot.adapters.satori.models import PageResult
    from nonebot.adapters.satori import Message, MessageSegment
    from nonebot.adapters.satori.models import InnerMessage as SatoriMessage
    from nonebot.adapters.satori.event import (
        MessageEvent,
        PublicMessageEvent,
        PrivateMessageEvent,
    )

    T = TypeVar("T")

    adapter = SupportedAdapters.satori
    register_satori = partial(register_ms_adapter, adapter)

    MessageFactory.register_adapter_message(SupportedAdapters.satori, Message)

    class SatoriMessageId(MessageId):
        adapter_name: Literal[adapter] = adapter

        message_id: str

    @register_satori(Text)
    def _text(t: Text) -> MessageSegment:
        return MessageSegment.text(t.data["text"])

    @register_satori(Image)
    async def _image(i: Image) -> MessageSegment:
        image = i.data["image"]
        if isinstance(image, str):
            # URL
            return MessageSegment.image(image)
        elif isinstance(image, bytes):
            # raw
            if img_format := guess_mime(image):
                return MessageSegment.image(raw=image, mime=img_format)
            else:
                raise ValueError("Cannot determine image format")
        elif isinstance(image, BytesIO):
            # raw
            if img_format := guess_mime(image):
                return MessageSegment.image(raw=image, mime=img_format)
            else:
                raise ValueError("Cannot determine image format")
        elif isinstance(image, Path):
            # path
            return MessageSegment.image(path=image)
        else:
            raise ValueError(f"Unsupported image data type: {type(image)}")

    @register_satori(Mention)
    async def _mention(m: Mention) -> MessageSegment:
        return MessageSegment.at(m.data["user_id"])

    @register_satori(MentionAll)
    async def _mention_all(m: MentionAll) -> MessageSegment:
        return MessageSegment.at_all(m.data["onlines_only"])

    @register_satori(Reply)
    async def _reply(r: Reply) -> MessageSegment:
        assert isinstance(mid := r.data["message_id"], SatoriMessageId)
        return MessageSegment.quote(mid.message_id)

    @register_target_extractor(PrivateMessageEvent)
    def _extract_private_msg_event(event: Event) -> PlatformTarget:
        assert isinstance(event, PrivateMessageEvent)
        if event.platform in [
            SatoriPlatform.QQ,
            SatoriPlatform.RED,
            SatoriPlatform.CHRONOCAT,
        ]:
            return TargetQQPrivate(user_id=int(event.get_user_id()))
        elif event.platform == SatoriPlatform.KOOK:
            return TargetKaiheilaPrivate(user_id=event.get_user_id())
        elif event.platform == SatoriPlatform.TELEGRAM:
            return TargetTelegramCommon(chat_id=event.get_user_id())
        elif event.platform == SatoriPlatform.FEISHU:
            return TargetFeishuPrivate(open_id=event.get_user_id())
        return TargetSatoriUnknown(platform=event.platform, channel_id=event.channel.id)

    @register_target_extractor(PublicMessageEvent)
    def _extract_group_msg_event(event: Event) -> PlatformTarget:
        assert isinstance(event, PublicMessageEvent)
        if event.platform in [
            SatoriPlatform.QQ,
            SatoriPlatform.RED,
            SatoriPlatform.CHRONOCAT,
        ]:
            return TargetQQGroup(group_id=int(event.channel.id))
        elif event.platform == SatoriPlatform.KOOK:
            return TargetKaiheilaChannel(channel_id=event.channel.id)
        # TODO: support telegram forum
        elif event.platform == SatoriPlatform.FEISHU:
            return TargetFeishuGroup(chat_id=event.channel.id)
        return TargetSatoriUnknown(platform=event.platform, channel_id=event.channel.id)

    @register_convert_to_arg(adapter, SupportedPlatform.qq_private)
    def _gen_qq_private(target: PlatformTarget) -> Dict[str, Any]:
        assert isinstance(target, TargetQQPrivate)
        return {"channel_id": f"private:{target.user_id}"}

    @register_convert_to_arg(adapter, SupportedPlatform.qq_group)
    def _gen_qq_group(target: PlatformTarget) -> Dict[str, Any]:
        assert isinstance(target, TargetQQGroup)
        return {"channel_id": str(target.group_id)}

    @register_convert_to_arg(adapter, SupportedPlatform.feishu_private)
    def _gen_feishu_private(target: PlatformTarget) -> Dict[str, Any]:
        assert isinstance(target, TargetFeishuPrivate)
        return {"channel_id": target.open_id}

    @register_convert_to_arg(adapter, SupportedPlatform.feishu_group)
    def _gen_feishu_group(target: PlatformTarget) -> Dict[str, Any]:
        assert isinstance(target, TargetFeishuGroup)
        return {"channel_id": target.chat_id}

    @register_convert_to_arg(adapter, SupportedPlatform.telegram_common)
    def _gen_telegram_common(target: PlatformTarget) -> Dict[str, Any]:
        assert isinstance(target, TargetTelegramCommon)
        return {"channel_id": target.chat_id}

    @register_convert_to_arg(adapter, SupportedPlatform.unknown_satori)
    def _to_unknow(target: PlatformTarget):
        assert isinstance(target, TargetSatoriUnknown)
        # TODO: 如果是私聊，需要先创建私聊会话
        if target.channel_id is None:
            raise NotImplementedError
        return {"channel_id": target.channel_id}

    class SatoriReceipt(Receipt):
        adapter_name: Literal[adapter] = adapter
        messages: List[SatoriMessage]

        async def revoke(self):
            for message in self.messages:
                assert message.channel
                await cast(BotSatori, self._get_bot()).message_delete(
                    channel_id=message.channel.id,
                    message_id=message.id,
                )

        @property
        def raw(self) -> List[SatoriMessage]:
            return self.messages

        def extract_message_id(self, index: int = 0) -> MessageId:
            """从 Receipt 中提取 MessageId

            Args:
                index (int, optional): 默认为0, 即提取第一条消息的 MessageId.
            """
            return SatoriMessageId(message_id=self.messages[index].id)

    @register_sender(SupportedAdapters.satori)
    async def send(
        bot,
        msg: MessageFactory,
        target: PlatformTarget,
        event: Optional[Event],
        at_sender: bool,
        reply: bool,
    ) -> SatoriReceipt:
        assert isinstance(bot, BotSatori)
        if event:
            assert isinstance(event, MessageEvent)
            full_msg = assamble_message_factory(
                msg,
                Mention(event.get_user_id()),
                Reply(SatoriMessageId(message_id=event.message.id)),
                at_sender,
                reply,
            )
        else:
            full_msg = msg
        message_to_send = Message()
        for message_segment_factory in full_msg:
            message_segment = await message_segment_factory.build(bot)
            message_to_send += message_segment

        if event:
            resp = await bot.send_message(
                message=message_to_send, channel_id=event.channel.id
            )
        else:
            resp = await bot.send_message(
                message=message_to_send, **target.arg_dict(bot)
            )

        return SatoriReceipt(bot_id=bot.self_id, messages=resp)

    @AggregatedMessageFactory.register_aggregated_sender(adapter)
    async def aggregate_send(
        bot: Bot,
        message_factories: List[MessageFactory],
        target: PlatformTarget,
        event: Optional[Event],
    ):
        assert isinstance(bot, BotSatori)

        msg_list: List[Message] = []
        for msg_fac in message_factories:
            msg = await msg_fac.build(bot)
            assert isinstance(msg, Message)
            msg_list.append(msg)

        message_to_send = Message()
        for msg in msg_list:
            message_to_send += MessageSegment.message(content=msg)

        if event:
            assert isinstance(event, MessageEvent)
            await bot.send_message(message=message_to_send, channel_id=event.channel.id)
        else:
            await bot.send_message(message=message_to_send, **target.arg_dict(bot))

    class PagedAPI(Generic[T], Protocol):
        def __call__(
            self, *, next_token: Optional[str] = None
        ) -> Awaitable[PageResult[T]]:
            ...

    async def _fetch_all(paged_api: PagedAPI[T]) -> List[T]:
        results = []
        # nonebor-adapter-satori < 0.10.2 的 `channel_list` API 会因为 next_token 为 None 而报错
        token = None
        while True:
            resp = await paged_api(next_token=token)
            results.extend(resp.data)
            if resp.next is None:
                logger.debug("No more pages to fetch")
                break
            token = resp.next
            logger.debug(f"Fetching next page with token: {token}")
        return results

    @register_list_targets(SupportedAdapters.satori)
    async def list_targets(bot: Bot) -> List[PlatformTarget]:
        assert isinstance(bot, BotSatori)

        targets = []
        # 获取群组列表
        try:
            guilds = await _fetch_all(bot.guild_list)
            for guild in guilds:
                channels = await _fetch_all(
                    partial(bot.channel_list, guild_id=guild.id)
                )
                for channel in channels:
                    if bot.platform in ["qq", "red", "chronocat"]:
                        target = TargetQQGroup(group_id=int(channel.id))
                    else:
                        target = TargetSatoriUnknown(
                            platform=bot.platform, channel_id=channel.id
                        )
                    targets.append(target)
        except ActionFailed as e:  # pragma: no cover
            logger.warning(
                f"Satori({bot.platform}) does not support fetching channel list: {e}"
            )

        # 获取好友列表
        try:
            users = await _fetch_all(bot.friend_list)
            for user in users:
                if bot.platform in ["qq", "red", "chronocat"]:
                    target = TargetQQPrivate(user_id=int(user.id))
                else:
                    target = TargetSatoriUnknown(platform=bot.platform, user_id=user.id)
                targets.append(target)
        except ActionFailed as e:  # pragma: no cover
            logger.warning(
                f"Satori({bot.platform}) does not support fetching friend list: {e}"
            )

        return targets

except ImportError:
    pass
except Exception as e:
    raise e
