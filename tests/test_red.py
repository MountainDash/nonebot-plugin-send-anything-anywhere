from datetime import datetime
from functools import partial

import httpx
from nonebug import App
from respx import MockRouter
from nonebot import get_adapter
from pytest_mock import MockerFixture
from nonebot.adapters.red import Bot, Adapter
from nonebot.adapters.red.config import BotInfo

from nonebot_plugin_saa.utils import SupportedAdapters

from .utils import assert_ms, mock_red_message_event

bot_info = BotInfo(port=1234, token="1234")
assert_red = partial(assert_ms, Bot, SupportedAdapters.red, info=bot_info)


async def test_text(app: App):
    from nonebot.adapters.red import MessageSegment

    from nonebot_plugin_saa import Text

    await assert_red(app, Text("123"), MessageSegment.text("123"))


async def test_image(app: App, respx_mock: MockRouter):
    from nonebot.adapters.red import MessageSegment

    from nonebot_plugin_saa import Image

    await assert_red(app, Image(b"123"), MessageSegment.image(b"123"))

    test = respx_mock.get("https://gchat.qpic.cn/test").mock(
        return_value=httpx.Response(204, content=b"321")
    )

    await assert_red(
        app,
        Image("https://gchat.qpic.cn/test"),
        MessageSegment.image(b"321"),
    )
    assert test.called


async def test_mention(app: App):
    from nonebot.adapters.red import MessageSegment

    from nonebot_plugin_saa import Mention

    await assert_red(app, Mention("123"), MessageSegment.at("123"))


async def test_reply(app: App):
    from nonebot.adapters.red import MessageSegment

    from nonebot_plugin_saa import Reply

    await assert_red(app, Reply("123"), MessageSegment.reply("123"))


async def test_send(app: App):
    from nonebot.adapters.red import Bot
    from nonebot import get_driver, on_message
    from nonebot.adapters.red.event import PrivateMessageEvent

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters

    matcher = on_message()

    @matcher.handle()
    async def process(msg: PrivateMessageEvent):
        await MessageFactory(Text("123")).send()

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.red)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, info=bot_info)
        msg_event = mock_red_message_event()
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "send_message",
            data={
                "chat_type": 1,
                "target": "1234",
                "elements": [{"elementType": 1, "textElement": {"content": "123"}}],
            },
            result=msg_event.dict(),
        )


async def test_send_aggreted_red(app: App, mocker: MockerFixture):
    from nonebot.adapters.red import Bot
    from nonebot import get_driver, on_message
    from nonebot.adapters.red.event import MessageEvent

    from nonebot_plugin_saa import Text, SupportedAdapters, AggregatedMessageFactory

    mocked_ranint = mocker.patch("random.randint", return_value=1)
    mocked_datetime = mocker.patch("nonebot_plugin_saa.adapters.red.datetime")
    mocked_datetime.now.return_value = datetime(2021, 1, 1, 0, 0, 0)

    matcher = on_message()

    @matcher.handle()
    async def process(msg: MessageEvent):
        await AggregatedMessageFactory([Text("123"), Text("456")]).send()

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.red)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, self_id="10", info=bot_info)
        msg_event = mock_red_message_event()

        ctx.should_call_api(
            "send_fake_forward",
            data={
                "chat_type": 1,
                "target": "1234",
                "source_chat_type": 1,
                "source_target": "1234",
                "elements": [
                    {
                        "head": {
                            "field2": "10",
                            "field8": {"field1": 10, "field4": "10"},
                        },
                        "content": {
                            "field1": 82,
                            "field4": 1,
                            "field5": 1,
                            "field6": 1609430400,
                            "field7": 1,
                            "field8": 0,
                            "field9": 0,
                            "field15": {"field1": 0, "field2": 0},
                        },
                        "body": {"richText": {"elems": [{"text": {"str": "123"}}]}},
                    },
                    {
                        "head": {
                            "field2": "10",
                            "field8": {"field1": 10, "field4": "10"},
                        },
                        "content": {
                            "field1": 82,
                            "field4": 1,
                            "field5": 2,
                            "field6": 1609430400,
                            "field7": 1,
                            "field8": 0,
                            "field9": 0,
                            "field15": {"field1": 0, "field2": 0},
                        },
                        "body": {"richText": {"elems": [{"text": {"str": "456"}}]}},
                    },
                ],
            },
            result=msg_event,
        )
        ctx.receive_event(bot, msg_event)

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.red)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, self_id="10", info=bot_info)
        msg_event = mock_red_message_event(group=True)

        ctx.should_call_api(
            "send_fake_forward",
            data={
                "chat_type": 2,
                "target": "1111",
                "source_chat_type": 2,
                "source_target": "1111",
                "elements": [
                    {
                        "head": {
                            "field2": "10",
                            "field8": {"field1": 10, "field4": "10"},
                        },
                        "content": {
                            "field1": 82,
                            "field4": 1,
                            "field5": 1,
                            "field6": 1609430400,
                            "field7": 1,
                            "field8": 0,
                            "field9": 0,
                            "field15": {"field1": 0, "field2": 0},
                        },
                        "body": {"richText": {"elems": [{"text": {"str": "123"}}]}},
                    },
                    {
                        "head": {
                            "field2": "10",
                            "field8": {"field1": 10, "field4": "10"},
                        },
                        "content": {
                            "field1": 82,
                            "field4": 1,
                            "field5": 2,
                            "field6": 1609430400,
                            "field7": 1,
                            "field8": 0,
                            "field9": 0,
                            "field15": {"field1": 0, "field2": 0},
                        },
                        "body": {"richText": {"elems": [{"text": {"str": "456"}}]}},
                    },
                ],
            },
            result=msg_event,
        )
        ctx.receive_event(bot, msg_event)

    mocked_ranint.assert_called()


async def test_send_with_reply(app: App):
    from nonebot.adapters.red import Bot
    from nonebot import get_driver, on_message
    from nonebot.adapters.red.event import PrivateMessageEvent

    from nonebot_plugin_saa import Text, MessageFactory, SupportedAdapters

    matcher = on_message()

    @matcher.handle()
    async def process(msg: PrivateMessageEvent):
        await MessageFactory(Text("123")).send(reply=True, at_sender=True)

    async with app.test_matcher(matcher) as ctx:
        adapter_obj = get_driver()._adapters[str(SupportedAdapters.red)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_obj, info=bot_info)
        msg_event = mock_red_message_event()
        ctx.receive_event(bot, msg_event)
        ctx.should_call_api(
            "send_message",
            data={
                "chat_type": 1,
                "target": "1234",
                "elements": [
                    {
                        "elementType": 7,
                        "replyElement": {
                            "sourceMsgIdInRecords": None,
                            "replayMsgSeq": "103",
                            "senderUid": None,
                        },
                    },
                    {"elementType": 1, "textElement": {"atType": 2, "atNtUin": "1234"}},
                    {"elementType": 1, "textElement": {"content": "123"}},
                ],
            },
            result=msg_event.dict(),
        )


async def test_send_active(app: App):
    from nonebot import get_driver

    from nonebot_plugin_saa import TargetQQGroup, MessageFactory, TargetQQPrivate

    async with app.test_api() as ctx:
        adapter_ob11 = get_driver()._adapters[str(SupportedAdapters.red)]
        bot = ctx.create_bot(base=Bot, adapter=adapter_ob11, info=bot_info)

        send_target_private = TargetQQPrivate(user_id=1122)
        ctx.should_call_api(
            "send_message",
            data={
                "chat_type": 1,
                "target": "1122",
                "elements": [{"elementType": 1, "textElement": {"content": "123"}}],
            },
            result=mock_red_message_event(),
        )
        await MessageFactory("123").send_to(send_target_private, bot)

        send_target_group = TargetQQGroup(group_id=1122)
        ctx.should_call_api(
            "send_message",
            data={
                "chat_type": 2,
                "target": "1122",
                "elements": [{"elementType": 1, "textElement": {"content": "123"}}],
            },
            result=mock_red_message_event(),
        )
        await MessageFactory("123").send_to(send_target_group, bot)


async def test_list_targets(app: App, mocker: MockerFixture):
    from nonebot_plugin_saa import TargetQQGroup, TargetQQPrivate
    from nonebot_plugin_saa.utils.auto_select_bot import get_bot, refresh_bots

    mocker.patch("nonebot_plugin_saa.utils.auto_select_bot.inited", True)

    async with app.test_api() as ctx:
        adapter = get_adapter(Adapter)
        bot = ctx.create_bot(base=Bot, adapter=adapter, info=bot_info)

        ctx.should_call_api(
            "get_groups",
            {},
            [
                {
                    "groupCode": "112",
                    "maxMember": 200,
                    "memberCount": 2,
                    "groupName": "uy/sun、小⑨",
                    "groupStatus": 0,
                    "memberRole": 2,
                    "isTop": False,
                    "toppedTimestamp": "0",
                    "privilegeFlag": 67633344,
                    "isConf": True,
                    "hasModifyConfGroupFace": False,
                    "hasModifyConfGroupName": False,
                    "remarkName": "",
                    "avatarUrl": "https://p.qlogo.cn/xxxx",
                    "hasMemo": False,
                    "groupShutupExpireTime": "0",
                    "personShutupExpireTime": "0",
                    "discussToGroupUin": "0",
                    "discussToGroupMaxMsgSeq": 0,
                    "discussToGroupTime": 0,
                }
            ],
        )
        ctx.should_call_api(
            "get_friends",
            {},
            [
                {
                    "uid": "4321",
                    "qid": "",
                    "uin": "1122",
                    "nick": "uy/sun",
                    "remark": "",
                    "longNick": "祝大家新年快乐！兔年大吉！",
                    "avatarUrl": "http://q.qlogo.cn/xxxx",
                    "birthday_year": 2023,
                    "birthday_month": 8,
                    "birthday_day": 30,
                    "sex": 1,
                    "topTime": "0",
                    "isBlock": False,
                    "isMsgDisturb": False,
                    "isSpecialCareOpen": False,
                    "isSpecialCareZone": False,
                    "ringId": "",
                    "status": 10,
                    "extStatus": 0,
                    "categoryId": 0,
                    "onlyChat": False,
                    "qzoneNotWatch": False,
                    "qzoneNotWatched": False,
                    "vipFlag": True,
                    "yearVipFlag": True,
                    "svipFlag": False,
                    "vipLevel": 7,
                }
            ],
        )
        await refresh_bots()

        send_target_private = TargetQQPrivate(user_id=1122)
        assert bot is get_bot(send_target_private)

        send_target_group = TargetQQGroup(group_id=112)
        assert bot is get_bot(send_target_group)


def test_extract_target(app: App):
    from nonebot_plugin_saa import TargetQQGroup, TargetQQPrivate, extract_target

    group_message_event = mock_red_message_event(True)
    assert extract_target(group_message_event) == TargetQQGroup(group_id=1111)

    private_message_event = mock_red_message_event(False)
    assert extract_target(private_message_event) == TargetQQPrivate(user_id=1234)
