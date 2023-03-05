import pytest
from nonebug import App


async def test_not_send_in_handler(app: App):
    from nonebot_plugin_saa import Text, MessageFactory

    msg = MessageFactory(Text("123"))
    with pytest.raises(RuntimeError):
        await msg.send()
