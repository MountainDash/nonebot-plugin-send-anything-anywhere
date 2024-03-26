import random
from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict, Type, Literal, cast

from nonebot import get_driver

if TYPE_CHECKING:
    from nonebug import App
    from nonebot.internal.adapter.bot import Bot
    from nonebot.adapters.qq import Message as QQMessage
    from nonebot.adapters.telegram import Message as TGMessage
    from nonebot.internal.adapter.message import MessageSegment
    from nonebot.adapters.onebot.v11 import Message as OB11Message
    from nonebot.adapters.onebot.v12 import Message as OB12Message
    from nonebot.adapters.dodo.models import MessageBody, MessageType
    from nonebot.adapters.telegram.event import MessageEvent as TGMessageEvent

    from nonebot_plugin_saa.abstract_factories import (
        SupportedAdapters,
        MessageSegmentFactory,
    )


async def assert_ms(
    bot_base: "Type[Bot]",
    adapter: "SupportedAdapters",
    app: "App",
    ms_factory: "MessageSegmentFactory",
    ms: "MessageSegment",
    **kwargs,
):
    if not kwargs:
        kwargs["self_id"] = "314159"

    async with app.test_api() as ctx:
        adapter_obj = get_driver()._adapters[str(adapter)]
        bot = ctx.create_bot(base=bot_base, adapter=adapter_obj, **kwargs)
        generated_ms = await ms_factory.build(bot)
        assert generated_ms.data == ms.data


def mock_dodo_message_event(message: "MessageBody", type: "MessageType", private=False):
    from nonebot.adapters.dodo.models import Sex, Member, Personal
    from nonebot.adapters.dodo.event import (
        EventType,
        ChannelMessageEvent,
        PersonalMessageEvent,
    )

    if not private:
        return ChannelMessageEvent(
            event_id="1234",
            event_type=EventType.MESSAGE,
            timestamp=datetime(2023, 11, 11),
            dodo_source_id="1111",
            island_source_id="2222",
            personal=Personal(
                nick_name="amiya",
                avatar_url="https://example.com/amiya.png",
                sex=Sex(1),
            ),
            message_id="33331",
            message_type=type,
            message_body=message,
            member=Member(nick_name="kal'tist", join_time=datetime(2020, 2, 2)),
            channel_id="5555",
        )
    else:
        return PersonalMessageEvent(
            event_id="1234",
            event_type=EventType.PERSONAL_MESSAGE,
            timestamp=datetime(2023, 11, 11),
            dodo_source_id="1111",
            personal=Personal(
                nick_name="amiya",
                avatar_url="https://example.com/amiya.png",
                sex=Sex(1),
            ),
            message_id="33332",
            message_type=type,
            message_body=message,
        )


def mock_obv11_message_event(message: "OB11Message", group=False):
    from nonebot.adapters.onebot.v11.event import Sender
    from nonebot.adapters.onebot.v11 import GroupMessageEvent as OB11GroupMessageEvent
    from nonebot.adapters.onebot.v11 import (
        PrivateMessageEvent as OB11PrivateMessageEvent,
    )

    if not group:
        return OB11PrivateMessageEvent(
            time=1122,
            self_id=2233,
            post_type="message",
            sub_type="",
            user_id=2233,
            message_type="private",
            message_id=random.randrange(0, 10000),
            message=message,
            original_message=message,
            raw_message=str(message),
            font=1,
            sender=Sender(user_id=2233),
            to_me=False,
        )
    else:
        return OB11GroupMessageEvent(
            time=1122,
            self_id=2233,
            group_id=3344,
            post_type="message",
            sub_type="",
            user_id=2233,
            message_type="group",
            message_id=random.randrange(0, 10000),
            message=message,
            original_message=message,
            raw_message=str(message),
            font=1,
            sender=Sender(user_id=2233),
            to_me=False,
        )


def mock_obv12_message_event(
    message: "OB12Message",
    detail_type: Literal[
        "private", "group", "channel", "qqguild_private", "qqguild_channel"
    ] = "private",
):
    from nonebot.adapters.onebot.v12.event import BotSelf
    from nonebot.adapters.onebot.v12 import (
        GroupMessageEvent,
        ChannelMessageEvent,
        PrivateMessageEvent,
    )

    if detail_type == "private":
        return PrivateMessageEvent(
            id=str(random.randint(0, 10000)),
            time=datetime.now(),
            type="message",
            detail_type="private",
            sub_type="",
            self=BotSelf(platform="qq", user_id="2233"),
            message_id=str(random.randrange(0, 10000)),
            message=message,
            original_message=message,
            alt_message=str(message),
            user_id="2233",
        )
    elif detail_type == "group":
        return GroupMessageEvent(
            id=str(random.randint(0, 10000)),
            time=datetime.now(),
            type="message",
            detail_type="group",
            sub_type="",
            self=BotSelf(platform="qq", user_id="2233"),
            message_id=str(random.randrange(0, 10000)),
            message=message,
            original_message=message,
            alt_message=str(message),
            user_id="2233",
            group_id="4455",
        )
    elif detail_type == "channel":
        return ChannelMessageEvent(
            id=str(random.randint(0, 10000)),
            time=datetime.now(),
            type="message",
            detail_type="channel",
            sub_type="",
            self=BotSelf(platform="qq", user_id="2233"),
            message_id=str(random.randrange(0, 10000)),
            message=message,
            original_message=message,
            alt_message=str(message),
            user_id="2233",
            guild_id="5566",
            channel_id="6677",
        )
    elif detail_type == "qqguild_private":
        return PrivateMessageEvent(
            id="1111",
            time=datetime.now(),
            type="message",
            detail_type="private",
            sub_type="",
            self=BotSelf(platform="qqguild", user_id="2233"),
            message_id=str(random.randrange(0, 10000)),
            message=message,
            original_message=message,
            alt_message=str(message),
            user_id="2233",
            qqguild={  # type: ignore
                "guild_id": "4455",
                "src_guild_id": "5566",
            },
        )
    else:
        return ChannelMessageEvent(
            id="1111",
            time=datetime.now(),
            type="message",
            detail_type="channel",
            sub_type="",
            self=BotSelf(platform="qqguild", user_id="2233"),
            message_id=str(random.randrange(0, 10000)),
            message=message,
            original_message=message,
            alt_message=str(message),
            user_id="2233",
            guild_id="5566",
            channel_id="6677",
        )


def mock_qq_guild_message_event(message: "QQMessage", direct=False):
    from nonebot.adapters.qq.models import User
    from nonebot.adapters.qq.event import EventType
    from nonebot.adapters.qq import MessageCreateEvent, DirectMessageCreateEvent

    if not direct:
        return MessageCreateEvent(
            __type__=EventType.MESSAGE_CREATE,
            id=str(random.randrange(0, 10000)),
            guild_id="1122",
            channel_id="2233",
            content=message.extract_content(),
            author=User(id="3344"),
        )
    else:
        return DirectMessageCreateEvent(
            __type__=EventType.DIRECT_MESSAGE_CREATE,
            id=str(random.randrange(0, 10000)),
            guild_id="1122",
            channel_id="2233",
            content=message.extract_content(),
            author=User(id="3344"),
        )


def mock_qq_message_event(message: "QQMessage", direct=False):
    from nonebot.adapters.qq.event import EventType
    from nonebot.adapters.qq.models import FriendAuthor, GroupMemberAuthor
    from nonebot.adapters.qq import C2CMessageCreateEvent, GroupAtMessageCreateEvent

    if not direct:
        return GroupAtMessageCreateEvent(
            __type__=EventType.GROUP_AT_MESSAGE_CREATE,
            id=str(random.randrange(0, 10000)),
            author=GroupMemberAuthor(id="3344", member_openid="3344"),
            group_openid="1122",
            content=message.extract_content(),
            timestamp="12345678",
        )
    else:
        return C2CMessageCreateEvent(
            __type__=EventType.C2C_MESSAGE_CREATE,
            id=str(random.randrange(0, 10000)),
            author=FriendAuthor(id="3344", user_openid="3344"),
            content=message.extract_content(),
            timestamp="12345678",
        )


def ob12_kwargs(platform="qq", impl="walle") -> Dict[str, Any]:
    return {"platform": platform, "impl": impl}


def mock_telegram_message_event(
    message: "TGMessage",
    ev_type: Literal["private", "group", "forum", "channel"] = "private",
    has_username: bool = True,
    **additional_kw,
) -> "TGMessageEvent":
    from nonebot.adapters.telegram.model import Chat, User
    from nonebot.adapters.telegram.event import (
        ChannelPostEvent,
        GroupMessageEvent,
        PrivateMessageEvent,
        ForumTopicMessageEvent,
    )

    chat_type = cast(
        Literal["private", "supergroup", "channel"],
        "supergroup" if ev_type in ["group", "forum"] else ev_type,
    )
    kwargs = {
        "message": message,
        "message_id": 415411,
        "date": 1451441541,
        "chat": Chat(id=1145141919810, type=chat_type),
        "from": User(
            id=114514,
            is_bot=False,
            first_name="homo",
            last_name="senpai",
            username="homo_senpai" if has_username else None,
        ),
        "forward_from": None,
        "forward_from_chat": None,
        "forward_from_message_id": None,
        "forward_signature": None,
        "forward_sender_name": None,
        "forward_date": None,
        "via_bot": None,
        "has_protected_content": None,
        "media_group_id": None,
        "author_signature": None,
        **additional_kw,
    }

    if ev_type == "channel":
        del kwargs["from"]
        return ChannelPostEvent(**kwargs)
    if ev_type == "forum":
        return ForumTopicMessageEvent(message_thread_id=1919081, **kwargs)
    if ev_type == "group":
        return GroupMessageEvent(**kwargs)
    return PrivateMessageEvent(**kwargs)


def mock_red_message_event(group=False):
    from nonebot.adapters.red import Message as RedMessage
    from nonebot.adapters.red.api.model import MsgType, ChatType, RoleInfo
    from nonebot.adapters.red import GroupMessageEvent as RedGroupMessageEvent
    from nonebot.adapters.red import PrivateMessageEvent as RedPrivateMessageEvent

    if not group:
        return RedPrivateMessageEvent(
            msgId="7272944767457625851",
            msgRandom="196942265",
            msgSeq="103",
            cntSeq="0",
            chatType=ChatType.FRIEND,
            msgType=MsgType.normal,
            subMsgType=1,
            sendType=0,
            senderUid="4321",
            senderUin="1234",
            peerUid="4321",
            peerUin="1234",
            channelId="",
            guildId="",
            guildCode="0",
            fromUid="0",
            fromAppid="0",
            msgTime="1693364414",
            msgMeta="0x",
            sendStatus=2,
            sendMemberName="",
            sendNickName="",
            guildName="",
            channelName="",
            elements=[],
            records=[],
            emojiLikesList=[],
            commentCnt="0",
            directMsgFlag=0,
            directMsgMembers=[],
            peerName="",
            editable=False,
            avatarMeta="",
            avatarPendant="",
            feedId="",
            roleId="0",
            timeStamp="0",
            isImportMsg=False,
            atType=0,
            roleType=0,
            fromChannelRoleInfo=RoleInfo(roleId="0", name="", color=0),
            fromGuildRoleInfo=RoleInfo(roleId="0", name="", color=0),
            levelRoleInfo=RoleInfo(roleId="0", name="", color=0),
            recallTime="0",
            isOnlineMsg=True,
            generalFlags="0x",
            clientSeq="27516",
            nameType=0,
            avatarFlag=0,
            message=RedMessage("321"),
            original_message=RedMessage("321"),
        )
    else:
        return RedGroupMessageEvent(
            msgId="7272944513098472702",
            msgRandom="1526531828",
            msgSeq="831",
            cntSeq="0",
            chatType=ChatType.GROUP,
            msgType=MsgType.normal,
            subMsgType=1,
            sendType=0,
            senderUid="4321",
            senderUin="1234",
            peerUid="1111",
            peerUin="1111",
            channelId="",
            guildId="",
            guildCode="0",
            fromUid="0",
            fromAppid="0",
            msgTime="1693364354",
            msgMeta="0x",
            sendStatus=2,
            sendMemberName="",
            sendNickName="uy/sun",
            guildName="",
            channelName="",
            elements=[],
            records=[],
            emojiLikesList=[],
            commentCnt="0",
            directMsgFlag=0,
            directMsgMembers=[],
            peerName="uy/sun",
            editable=False,
            avatarMeta="",
            avatarPendant="",
            feedId="",
            roleId="0",
            timeStamp="0",
            isImportMsg=False,
            atType=0,
            roleType=None,
            fromChannelRoleInfo=RoleInfo(roleId="0", name="", color=0),
            fromGuildRoleInfo=RoleInfo(roleId="0", name="", color=0),
            levelRoleInfo=RoleInfo(roleId="0", name="", color=0),
            recallTime="0",
            isOnlineMsg=True,
            generalFlags="0x",
            clientSeq="0",
            nameType=0,
            avatarFlag=0,
            message=RedMessage("321"),
            original_message=RedMessage("321"),
        )
