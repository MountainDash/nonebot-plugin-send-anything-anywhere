from functools import partial

from nonebug import App
from nonebot import get_adapter
from pytest_mock import MockerFixture
from nonebot.adapters.onebot.v11 import Bot, Adapter

from nonebot_plugin_saa.utils import SupportedAdapters

from .utils import assert_ms, mock_obv11_message_event

assert_onebot_v11 = partial(assert_ms, Bot, SupportedAdapters.onebot_v11)


async def test_text(app: App):
    from nonebot.adapters.onebot.v11 import MessageSegment

    from nonebot_plugin_saa import Text

    await assert_onebot_v11(app, Text("123"), MessageSegment.text("123"))


async def test_image(app: App):
    from nonebot.adapters.onebot.v11 import MessageSegment

    from nonebot_plugin_saa import Image

    await assert_onebot_v11(app, Image("123"), MessageSegment.image("123"))


async def test_mention(app: App):
    from nonebot.adapters.onebot.v11 import MessageSegment

    from nonebot_plugin_saa import Mention

    await assert_onebot_v11(app, Mention("123"), MessageSegment.at("123"))


async def test_reply(app: App):
    from nonebot.adapters.onebot.v11 import MessageSegment

    from nonebot_plugin_saa import Reply

    await assert_onebot_v11(app, Reply(123), MessageSegment.reply(123))


async def test_send(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.onebot.v11 import Bot, Message, PrivateMessageEvent

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters

    matcher = on_message()

    @matcher.handle()
    async def process(msg: PrivateMessageEvent):
        await MessageFactory(Text("123")).send()

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.onebot_v11)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj)
        msg_event = mock_obv11_message_event(Message("321"))
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "send_msg",
            data={
                "message": Message("123"),
                "user_id": 2233,
                "message_type": "private",
            },
            result={
                "message_id": 667788,
            },
        )


async def test_send_with_reply_and_revoke(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.onebot.v11 import (
        Bot,
        Message,
        MessageSegment,
        PrivateMessageEvent,
    )

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters

    matcher = on_message()

    @matcher.handle()
    async def process(msg: PrivateMessageEvent):
        receipt = await MessageFactory(Text("123")).send(reply=True, at_sender=True)
        await receipt.revoke()

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.onebot_v11)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj)
        msg_event = mock_obv11_message_event(Message("321"))
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "send_msg",
            data={
                "message": Message(
                    [
                        MessageSegment.reply(msg_event.message_id),
                        MessageSegment.at(msg_event.user_id),
                        MessageSegment.text("123"),
                    ]
                ),
                "user_id": 2233,
                "message_type": "private",
            },
            result={"message_id": 66778},
        )

        ctx.should_call_api("delete_msg", data={"message_id": 66778})


async def test_send_active(app: App):
    from nonebot import get_driver
    from nonebot.adapters.onebot.v11 import Message

    from nonebot_plugin_saa import TargetQQGroup, MessageFactory, TargetQQPrivate

    async with app.test_api() as ctx:
        adapter_ob11 = get_driver()._adapters[str(SupportedAdapters.onebot_v11)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_ob11)

        send_target_private = TargetQQPrivate(user_id=1122)
        ctx.should_call_api(
            "send_msg",
            data={
                "message": Message("123"),
                "user_id": 1122,
                "message_type": "private",
            },
            result={"message_id": 79767},
        )
        await MessageFactory("123").send_to(send_target_private, bot)

        send_target_group = TargetQQGroup(group_id=1122)
        ctx.should_call_api(
            "send_msg",
            data={
                "message": Message("123"),
                "group_id": 1122,
                "message_type": "group",
            },
            result={"message_id": 1232451},
        )
        await MessageFactory("123").send_to(send_target_group, bot)


async def test_send_aggreted_ob11(app: App):
    from nonebot import get_driver, on_message
    from nonebot.adapters.onebot.v11 import Bot, Message, MessageEvent, MessageSegment

    from nonebot_plugin_saa import Text, SupportedAdapters, AggregatedMessageFactory

    matcher = on_message()

    @matcher.handle()
    async def process(msg: MessageEvent):
        await AggregatedMessageFactory([Text("123"), Text("456")]).send()

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.onebot_v11)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, self_id="9988")
        msg_event = mock_obv11_message_event(Message("321"))

        ctx.should_call_api(
            "get_login_info",
            data={},
            result={"user_id": int(bot.self_id), "nickname": "potato"},
        )
        ctx.should_call_api(
            "send_private_forward_msg",
            data={
                "messages": Message(
                    [
                        MessageSegment.node_custom(
                            user_id=int(bot.self_id),
                            nickname="potato",
                            content=Message("123"),
                        ),
                        MessageSegment.node_custom(
                            user_id=int(bot.self_id),
                            nickname="potato",
                            content=Message("456"),
                        ),
                    ]
                ),
                "user_id": 2233,
            },
            result=None,
        )
        ctx.receive_event(bot, msg_event)

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.onebot_v11)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, self_id="9988")
        msg_event = mock_obv11_message_event(Message("321"), group=True)

        ctx.should_call_api(
            "get_login_info",
            data={},
            result={"user_id": int(bot.self_id), "nickname": "potato"},
        )
        ctx.should_call_api(
            "send_group_forward_msg",
            data={
                "messages": Message(
                    [
                        MessageSegment.node_custom(
                            user_id=int(bot.self_id),
                            nickname="potato",
                            content=Message("123"),
                        ),
                        MessageSegment.node_custom(
                            user_id=int(bot.self_id),
                            nickname="potato",
                            content=Message("456"),
                        ),
                    ]
                ),
                "group_id": 3344,
            },
            result=None,
        )
        ctx.receive_event(bot, msg_event)


async def test_list_targets(app: App, mocker: MockerFixture):
    from nonebot_plugin_saa import TargetQQGroup, TargetQQPrivate
    from nonebot_plugin_saa.auto_select_bot import get_bot, refresh_bots

    mocker.patch("nonebot_plugin_saa.auto_select_bot.inited", True)

    async with app.test_api() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter)

        ctx.should_call_api("get_group_list", {}, [{"group_id": 112}])
        ctx.should_call_api("get_friend_list", {}, [{"user_id": 1122}])
        await refresh_bots()

        send_target_private = TargetQQPrivate(user_id=1122)
        assert bot is get_bot(send_target_private)

        send_target_group = TargetQQGroup(group_id=112)
        assert bot is get_bot(send_target_group)


def test_extract_target(app: App):
    from nonebot.adapters.onebot.v11.event import File, Sender
    from nonebot.adapters.onebot.v11 import (
        Message,
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

    from nonebot_plugin_saa import TargetQQGroup, TargetQQPrivate, extract_target

    sender = Sender(user_id=3344)
    group_message_event = GroupMessageEvent(
        group_id=1122,
        time=1122,
        self_id=2233,
        post_type="message",
        sub_type="",
        user_id=3344,
        message_id=4455,
        message=Message("123"),
        original_message=Message("123"),
        message_type="group",
        raw_message="123",
        font=1,
        sender=sender,
    )
    assert extract_target(group_message_event) == TargetQQGroup(group_id=1122)

    private_message_event = PrivateMessageEvent(
        time=1122,
        self_id=2233,
        post_type="message",
        sub_type="",
        user_id=3344,
        message_id=4455,
        message=Message("123"),
        original_message=Message("123"),
        message_type="private",
        raw_message="123",
        font=1,
        sender=sender,
    )
    assert extract_target(private_message_event) == TargetQQPrivate(user_id=3344)

    friend_add_notice_event = FriendAddNoticeEvent(
        time=1122,
        self_id=2233,
        post_type="notice",
        notice_type="friend_add",
        user_id=3344,
    )
    assert extract_target(friend_add_notice_event) == TargetQQPrivate(user_id=3344)

    friend_recall_notice_event = FriendRecallNoticeEvent(
        time=1122,
        self_id=2233,
        post_type="notice",
        notice_type="friend_recall",
        user_id=3344,
        message_id=4455,
    )
    assert extract_target(friend_recall_notice_event) == TargetQQPrivate(user_id=3344)

    group_ban_notice_event = GroupBanNoticeEvent(
        time=1122,
        self_id=2233,
        post_type="notice",
        notice_type="group_ban",
        sub_type="",
        group_id=1122,
        operator_id=3344,
        user_id=5566,
        duration=10,
    )
    assert extract_target(group_ban_notice_event) == TargetQQGroup(group_id=1122)

    group_recall_notice_event = GroupRecallNoticeEvent(
        time=1122,
        self_id=2233,
        post_type="notice",
        notice_type="group_recall",
        group_id=1122,
        operator_id=3344,
        user_id=5566,
        message_id=4455,
    )
    assert extract_target(group_recall_notice_event) == TargetQQGroup(group_id=1122)

    group_admin_notice_event = GroupAdminNoticeEvent(
        time=1122,
        self_id=2233,
        post_type="notice",
        notice_type="group_admin",
        sub_type="",
        group_id=1122,
        user_id=5566,
    )
    assert extract_target(group_admin_notice_event) == TargetQQGroup(group_id=1122)

    group_decrease_notice_event = GroupDecreaseNoticeEvent(
        time=1122,
        self_id=2233,
        post_type="notice",
        notice_type="group_decrease",
        sub_type="",
        group_id=1122,
        operator_id=3344,
        user_id=5566,
    )
    assert extract_target(group_decrease_notice_event) == TargetQQGroup(group_id=1122)

    group_increase_notice_event = GroupIncreaseNoticeEvent(
        time=1122,
        self_id=2233,
        post_type="notice",
        notice_type="group_increase",
        sub_type="",
        group_id=1122,
        operator_id=3344,
        user_id=5566,
    )
    assert extract_target(group_increase_notice_event) == TargetQQGroup(group_id=1122)

    group_upload_notice_event = GroupUploadNoticeEvent(
        time=1122,
        self_id=2233,
        post_type="notice",
        notice_type="group_upload",
        group_id=1122,
        user_id=3344,
        file=File(id="4455", name="123", size=10, busid=6677),
    )
    assert extract_target(group_upload_notice_event) == TargetQQGroup(group_id=1122)

    honor_notify_event = HonorNotifyEvent(
        time=1122,
        self_id=2233,
        post_type="notice",
        notice_type="notify",
        sub_type="honor",
        group_id=1122,
        user_id=3344,
        honor_type="talkative",
    )
    assert extract_target(honor_notify_event) == TargetQQGroup(group_id=1122)

    lucky_king_notify_event = LuckyKingNotifyEvent(
        time=1122,
        self_id=2233,
        post_type="notice",
        notice_type="notify",
        sub_type="lucky_king",
        group_id=1122,
        user_id=3344,
        target_id=5566,
    )
    assert extract_target(lucky_king_notify_event) == TargetQQGroup(group_id=1122)

    friend_request_event = FriendRequestEvent(
        time=1122,
        self_id=2233,
        post_type="request",
        request_type="friend",
        user_id=3344,
        comment="123",
        flag="2233",
    )
    assert extract_target(friend_request_event) == TargetQQPrivate(user_id=3344)

    group_request_event = GroupRequestEvent(
        time=1122,
        self_id=2233,
        post_type="request",
        request_type="group",
        sub_type="",
        group_id=1122,
        user_id=3344,
        comment="123",
        flag="2233",
    )
    assert extract_target(group_request_event) == TargetQQGroup(group_id=1122)

    poke_notify_event = PokeNotifyEvent(
        time=1122,
        self_id=2233,
        post_type="notice",
        notice_type="notify",
        sub_type="poke",
        group_id=1122,
        user_id=3344,
        target_id=5566,
    )
    assert extract_target(poke_notify_event) == TargetQQGroup(group_id=1122)

    poke_notify_event = PokeNotifyEvent(
        time=1122,
        self_id=2233,
        post_type="notice",
        notice_type="notify",
        sub_type="poke",
        group_id=None,
        user_id=3344,
        target_id=5566,
    )
    assert extract_target(poke_notify_event) == TargetQQPrivate(user_id=3344)
