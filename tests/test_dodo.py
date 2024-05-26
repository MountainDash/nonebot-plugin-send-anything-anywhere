from datetime import datetime
from functools import partial

import respx
import pytest
from nonebug import App
from httpx import Response
from nonebot.compat import model_dump
from pytest_mock import MockerFixture
from nonebot.exception import ActionFailed
from nonebot import get_driver, get_adapter
from nonebot.adapters.dodo import Bot, Adapter
from nonebot.adapters.dodo.config import BotConfig

from .utils import assert_ms, mock_dodo_message_event

dodo_bot_config = BotConfig(client_id="112233", token="3.14159")
dodo_kwargs = {
    "self_id": "123456",
    "bot_config": dodo_bot_config,
}


@pytest.fixture
def assert_dodo(app: App):
    from nonebot_plugin_saa import SupportedAdapters

    return partial(
        assert_ms,
        Bot,
        SupportedAdapters.dodo,
        bot_config=dodo_bot_config,
    )


async def test_text(app: App, assert_dodo):
    from nonebot.adapters.dodo import MessageSegment

    from nonebot_plugin_saa import Text

    await assert_dodo(app, Text("test"), MessageSegment.text("test"))


@respx.mock
async def test_image(app: App):
    from nonebot.adapters.dodo import MessageSegment
    from nonebot.adapters.dodo.models import PictureInfo

    from nonebot_plugin_saa import Image, SupportedAdapters

    image_route = respx.get("https://example.com/amiya.png")
    upload_route = respx.post(
        "https://botopen.imdodo.com/api/v2/resource/picture/upload"
    )

    image_route.mock(return_value=Response(200, content=b"amiya"))
    upload_route.mock(
        return_value=Response(
            200,
            json=model_dump(
                PictureInfo(url="https://im.dodo.com/amiya.png", width=191, height=223)
            ),
        )
    )
    async with app.test_api() as ctx:
        adapter = get_driver()._adapters[SupportedAdapters.dodo]
        bot = ctx.create_bot(base=Bot, adapter=adapter, **dodo_kwargs)

        ctx.should_call_api(
            "set_resouce_picture_upload",
            data={"file": b"amiya", "file_name": "image.png"},
            result=PictureInfo(
                url="https://im.dodo.com/amiya.png", width=191, height=223
            ),
        )

        generated_ms = await Image("https://example.com/amiya.png").build(bot)
        assert generated_ms == MessageSegment.picture(
            url="https://im.dodo.com/amiya.png", width=191, height=223
        )

    image_route.mock(return_value=Response(400, content=b"amiya"))
    with pytest.raises(RuntimeError):
        await Image("https://example.com/amiya.png").build(bot)

    image_route.mock(return_value=Response(200, content=b"amiya"))
    upload_route.mock(
        return_value=Response(400, json={"status": 400, "message": "amiya"})
    )
    with pytest.raises(ActionFailed):
        await Image("https://example.com/amiya.png").build(bot)


async def test_mention(app: App, assert_dodo):
    from nonebot.adapters.dodo import MessageSegment

    from nonebot_plugin_saa import Mention

    await assert_dodo(app, Mention("123456"), MessageSegment.at_user("123456"))


async def test_mention_all(app: App, assert_dodo):
    from nonebot.adapters.dodo import MessageSegment

    from nonebot_plugin_saa import MentionAll

    await assert_dodo(app, MentionAll(), MessageSegment.text(""))


async def test_reply(app: App, assert_dodo):
    from nonebot.adapters.dodo import MessageSegment

    from nonebot_plugin_saa import Reply
    from nonebot_plugin_saa.adapters.dodo import DodoMessageId

    await assert_dodo(
        app, Reply(DodoMessageId(message_id="1111")), MessageSegment.reference("1111")
    )


async def test_send(app: App):
    from nonebot.adapters.dodo import Bot
    from nonebot import get_driver, on_message
    from nonebot.adapters.dodo.models import MessageType, TextMessage, MessageReturn

    from nonebot_plugin_saa import Text, SupportedAdapters

    matcher = on_message()

    @matcher.handle()
    async def _():
        await Text("amiya").send()

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[SupportedAdapters.dodo]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **dodo_kwargs)
        msg_event = mock_dodo_message_event(
            TextMessage(content="aa"), type=MessageType(1)
        )
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "set_channel_message_send",
            data={
                "channel_id": "5555",
                "message_type": MessageType.TEXT,
                "message_body": TextMessage(content="amiya"),
                "referenced_message_id": None,
            },
            result=MessageReturn(message_id="33331"),
        )


async def test_extract_message_id(app: App):
    from nonebot.adapters.dodo import Bot
    from nonebot import get_driver, on_message
    from nonebot.adapters.dodo.models import MessageType, TextMessage, MessageReturn

    from nonebot_plugin_saa import Text, SupportedAdapters
    from nonebot_plugin_saa.adapters.dodo import DodoReceipt, DodoMessageId

    matcher = on_message()

    @matcher.handle()
    async def _():
        receipt = await Text("amiya").send()
        assert isinstance(receipt, DodoReceipt)
        assert receipt.extract_message_id() == DodoMessageId(message_id="33331")

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[SupportedAdapters.dodo]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **dodo_kwargs)
        msg_event = mock_dodo_message_event(
            TextMessage(content="aa"), type=MessageType(1)
        )
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "set_channel_message_send",
            data={
                "channel_id": "5555",
                "message_type": MessageType.TEXT,
                "message_body": TextMessage(content="amiya"),
                "referenced_message_id": None,
            },
            result=MessageReturn(message_id="33331"),
        )


async def test_send_with_reply_and_receipt(app: App):
    from nonebot import on_message
    from nonebot.adapters.dodo import Bot, Message, MessageSegment
    from nonebot.adapters.dodo.models import MessageType, TextMessage, MessageReturn

    from nonebot_plugin_saa import Text, SupportedAdapters
    from nonebot_plugin_saa.adapters.dodo import DodoReceipt

    matcher = on_message()

    @matcher.handle()
    async def _():
        receipt = await Text("amiya").send()
        assert isinstance(receipt, DodoReceipt)
        await receipt.edit(mesaage_body=TextMessage(content="kal'tist"))
        await receipt.pin()
        await receipt.revoke(reason="test")
        assert receipt.raw == "33331"

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[SupportedAdapters.dodo]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **dodo_kwargs)
        msg_event = mock_dodo_message_event(
            Message(
                [
                    MessageSegment.text("aa"),
                    MessageSegment.reference("1111"),
                ]
            ).to_message_body()[0],
            type=MessageType.TEXT,
        )
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "set_channel_message_send",
            data={
                "channel_id": "5555",
                "message_type": MessageType.TEXT,
                "message_body": Message(
                    [
                        MessageSegment.text("amiya"),
                        MessageSegment.reference("1111"),
                    ]
                ).to_message_body()[0],
                "referenced_message_id": None,
            },
            result=MessageReturn(message_id="33331"),
        )
        ctx.should_call_api(
            "set_channel_message_edit",
            data={
                "message_id": "33331",
                "message_body": TextMessage(content="kal'tist"),
            },
        )
        ctx.should_call_api(
            "set_channel_message_top",
            data={
                "message_id": "33331",
                "is_cancel": False,
            },
        )
        ctx.should_call_api(
            "set_channel_message_withdraw",
            data={
                "message_id": "33331",
                "reason": "test",
            },
        )


async def test_send_active(app: App):
    from nonebot import get_driver
    from nonebot.adapters.dodo.models import MessageType, TextMessage, MessageReturn

    from nonebot_plugin_saa import (
        MessageFactory,
        SupportedAdapters,
        TargetDoDoChannel,
        TargetDoDoPrivate,
    )

    async with app.test_api() as ctx:
        adapter_obj = get_driver()._adapters[SupportedAdapters.dodo]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, **dodo_kwargs)

        send_target_channel = TargetDoDoChannel(channel_id="55552")
        send_target_private = TargetDoDoPrivate(
            dodo_source_id="5555", island_source_id="55551"
        )
        send_target_channel_private = TargetDoDoChannel(
            channel_id="55552", dodo_source_id="5555"
        )

        ctx.should_call_api(
            "set_channel_message_send",
            data={
                "channel_id": "55552",
                "message_type": MessageType.TEXT,
                "message_body": TextMessage(content="kal'tist"),
                "referenced_message_id": None,
            },
            result=MessageReturn(message_id="33331"),
        )
        await MessageFactory("kal'tist").send_to(send_target_channel, bot)

        ctx.should_call_api(
            "set_personal_message_send",
            data={
                "dodo_source_id": "5555",
                "island_source_id": "55551",
                "message_type": MessageType.TEXT,
                "message_body": TextMessage(content="kal'tist"),
            },
            result=MessageReturn(message_id="33331"),
        )
        await MessageFactory("kal'tist").send_to(send_target_private, bot)

        ctx.should_call_api(
            "set_channel_message_send",
            data={
                "channel_id": "55552",
                "message_type": MessageType.TEXT,
                "message_body": TextMessage(content="kal'tist"),
                "referenced_message_id": None,
                "dodo_source_id": "5555",
            },
            result=MessageReturn(message_id="33331"),
        )
        await MessageFactory("kal'tist").send_to(send_target_channel_private, bot)


async def test_list_targets(app: App, mocker: MockerFixture):
    from nonebot.adapters.dodo.models import IslandInfo, ChannelInfo, ChannelType

    from nonebot_plugin_saa import TargetDoDoChannel
    from nonebot_plugin_saa.auto_select_bot import get_bot, refresh_bots

    mocker.patch("nonebot_plugin_saa.auto_select_bot.inited", True)

    async with app.test_api() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter, **dodo_kwargs)

        ctx.should_call_api(
            "get_island_list",
            data={},
            result=[
                IslandInfo(
                    island_source_id="5555",
                    island_name="amiya",
                    cover_url="https://example.com/amiya.png",
                    member_count=1,
                    online_member_count=1,
                    default_channel_id="6666",
                    system_channel_id="7777",
                )
            ],
        )
        ctx.should_call_api(
            "get_channel_list",
            data={"island_source_id": "5555"},
            result=[
                ChannelInfo(
                    channel_id="6666",
                    channel_name="amiya",
                    channel_type=ChannelType.TEXT,
                    default_flag=True,
                    group_id="8888",
                    group_name="amiya",
                )
            ],
        )
        await refresh_bots()

        send_target_channel = TargetDoDoChannel(channel_id="6666")
        assert get_bot(send_target_channel) is bot

        # TODO: test private


async def test_get_message_id(app: App):
    from nonebot.adapters.dodo.event import EventType, ChannelMessageEvent
    from nonebot.adapters.dodo.models import (
        Sex,
        Member,
        Personal,
        MessageType,
        TextMessage,
    )

    from nonebot_plugin_saa.registries import get_message_id
    from nonebot_plugin_saa.adapters.dodo import DodoMessageId

    cme = ChannelMessageEvent(
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
        message_type=MessageType(1),
        message_body=TextMessage(content="aa"),
        member=Member(nick_name="kal'tist", join_time=datetime(2020, 2, 2)),
        channel_id="5555",
    )

    assert get_message_id(cme) == DodoMessageId(message_id="33331")


async def test_extract_target(app: App):
    from nonebot.adapters.dodo.models import (
        Sex,
        Gift,
        Emoji,
        Member,
        FormData,
        ListData,
        Personal,
        TargetType,
        MessageType,
        TextMessage,
        ReactionType,
        ReactionTarget,
    )
    from nonebot.adapters.dodo.event import (
        EventType,
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

    from nonebot_plugin_saa import TargetDoDoChannel, TargetDoDoPrivate, extract_target

    cme = ChannelMessageEvent(
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
        message_type=MessageType(1),
        message_body=TextMessage(content="aa"),
        member=Member(nick_name="kal'tist", join_time=datetime(2020, 2, 2)),
        channel_id="5555",
    )
    assert extract_target(cme) == TargetDoDoChannel(channel_id="5555")

    pme = PersonalMessageEvent(
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
        message_type=MessageType(1),
        message_body=TextMessage(content="aa"),
        island_source_id="5555",
    )
    assert extract_target(pme) == TargetDoDoPrivate(
        island_source_id="5555", dodo_source_id="1111"
    )

    pme2 = PersonalMessageEvent(
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
        message_type=MessageType(1),
        message_body=TextMessage(content="aa"),
    )
    with pytest.raises(ValueError):
        extract_target(pme2)

    gse = GiftSendEvent(
        event_id="1234",
        event_type=EventType.GIFT_SEND,
        timestamp=datetime(2023, 11, 11),
        dodo_source_id="1111",
        island_source_id="5555",
        channel_id="6666",
        order_no="7777",
        target_type=TargetType(1),
        target_id="8888",
        total_amount=1.0,
        gift=Gift(id="99", name="66", count=1),
        island_ratio=1.0,
        island_income=1.0,
        dodo_island_nick_name="amiya",
        to_dodo_source_id="1111",
        to_dodo_island_nick_name="kal'tist",
        to_dodo_ratio=1.0,
        to_dodo_income=1.0,
    )
    assert extract_target(gse) == TargetDoDoChannel(channel_id="6666")

    cae = ChannelArticleEvent(
        event_id="1234",
        event_type=EventType.CHANNEL_ARTICLE,
        timestamp=datetime(2023, 11, 11),
        dodo_source_id="1111",
        island_source_id="5555",
        channel_id="6666",
        artical_id="7777",
        image_list=["https://example.com/amiya.png"],
        content="aa",
        personal=Personal(
            nick_name="amiya",
            avatar_url="https://example.com/amiya.png",
            sex=Sex(1),
        ),
        member=Member(nick_name="kal'tist", join_time=datetime(2020, 2, 2)),
        title="aa",
    )
    assert extract_target(cae) == TargetDoDoChannel(channel_id="6666")

    mre = MessageReactionEvent(
        event_id="1234",
        event_type=EventType.MESSAGE_REACTION,
        timestamp=datetime(2023, 11, 11),
        dodo_source_id="1111",
        island_source_id="5555",
        channel_id="6666",
        message_id="7777",
        personal=Personal(
            nick_name="amiya",
            avatar_url="https://example.com/amiya.png",
            sex=Sex(1),
        ),
        member=Member(nick_name="kal'tist", join_time=datetime(2020, 2, 2)),
        reaction_target=ReactionTarget(type=1, id="8888"),
        reaction_emoji=Emoji(id="9999", type=1),
        reaction_type=ReactionType(1),
    )
    assert extract_target(mre) == TargetDoDoChannel(channel_id="6666")

    cmfse = CardMessageFormSubmitEvent(
        event_id="1234",
        event_type=EventType.CARD_MESSAGE_FORM_SUBMIT,
        timestamp=datetime(2023, 11, 11),
        dodo_source_id="1111",
        island_source_id="5555",
        channel_id="6666",
        message_id="7777",
        personal=Personal(
            nick_name="amiya",
            avatar_url="https://example.com/amiya.png",
            sex=Sex(1),
        ),
        member=Member(nick_name="kal'tist", join_time=datetime(2020, 2, 2)),
        interact_custom_id="8888",
        form_data=[FormData(key="a", value="b")],
    )
    assert extract_target(cmfse) == TargetDoDoChannel(channel_id="6666")

    cmlse = CardMessageListSubmitEvent(
        event_id="1234",
        event_type=EventType.CARD_MESSAGE_LIST_SUBMIT,
        timestamp=datetime(2023, 11, 11),
        dodo_source_id="1111",
        island_source_id="5555",
        channel_id="6666",
        message_id="7777",
        personal=Personal(
            nick_name="amiya",
            avatar_url="https://example.com/amiya.png",
            sex=Sex(1),
        ),
        member=Member(nick_name="kal'tist", join_time=datetime(2020, 2, 2)),
        interact_custom_id="8888",
        list_data=[ListData(name="a")],
    )
    assert extract_target(cmlse) == TargetDoDoChannel(channel_id="6666")

    cace = ChannelArticleCommentEvent(
        event_id="1234",
        event_type=EventType.CHANNEL_ARTICLE_COMMENT,
        timestamp=datetime(2023, 11, 11),
        dodo_source_id="1111",
        island_source_id="5555",
        channel_id="6666",
        personal=Personal(
            nick_name="amiya",
            avatar_url="https://example.com/amiya.png",
            sex=Sex(1),
        ),
        member=Member(nick_name="kal'tist", join_time=datetime(2020, 2, 2)),
        artical_id="8888",
        comment_id="9999",
        reply_id="1111",
        image_list=["https://example.com/amiya.png"],
        content="aa",
    )
    assert extract_target(cace) == TargetDoDoChannel(channel_id="6666")

    cmbce = CardMessageButtonClickEvent(
        event_id="1234",
        event_type=EventType.CARD_MESSAGE_BUTTON_CLICK,
        timestamp=datetime(2023, 11, 11),
        dodo_source_id="1111",
        island_source_id="5555",
        channel_id="6666",
        message_id="7777",
        personal=Personal(
            nick_name="amiya",
            avatar_url="https://example.com/amiya.png",
            sex=Sex(1),
        ),
        member=Member(nick_name="kal'tist", join_time=datetime(2020, 2, 2)),
        interact_custom_id="8888",
        value="9999",
    )
    assert extract_target(cmbce) == TargetDoDoChannel(channel_id="6666")

    cvmje = ChannelVoiceMemberJoinEvent(
        event_id="1234",
        event_type=EventType.CHANNEL_VOICE_MEMBER_JOIN,
        timestamp=datetime(2023, 11, 11),
        dodo_source_id="1111",
        island_source_id="5555",
        channel_id="6666",
        personal=Personal(
            nick_name="amiya",
            avatar_url="https://example.com/amiya.png",
            sex=Sex(1),
        ),
        member=Member(nick_name="kal'tist", join_time=datetime(2020, 2, 2)),
    )
    assert extract_target(cvmje) == TargetDoDoChannel(channel_id="6666")

    cvmle = ChannelVoiceMemberLeaveEvent(
        event_id="1234",
        event_type=EventType.CHANNEL_VOICE_MEMBER_LEAVE,
        timestamp=datetime(2023, 11, 11),
        dodo_source_id="1111",
        island_source_id="5555",
        channel_id="6666",
        personal=Personal(
            nick_name="amiya",
            avatar_url="https://example.com/amiya.png",
            sex=Sex(1),
        ),
        member=Member(nick_name="kal'tist", join_time=datetime(2020, 2, 2)),
    )
    assert extract_target(cvmle) == TargetDoDoChannel(channel_id="6666")
