import pytest
from nonebug import App


def test_type_message_id_check(app: App):
    from nonebot_plugin_saa.utils import type_message_id_check
    from nonebot_plugin_saa.adapters.onebot_v11 import OB11MessageId
    from nonebot_plugin_saa.adapters.onebot_v12 import OB12MessageId
    from nonebot_plugin_saa.abstract_factories import SupportedAdapters
    from nonebot_plugin_saa.utils.exceptions import UnexpectedMessageIdType

    message_id = OB11MessageId(
        adapter_name=SupportedAdapters.onebot_v11, message_id=1919810
    )

    assert type_message_id_check(OB11MessageId, message_id) == message_id

    with pytest.raises(UnexpectedMessageIdType):
        type_message_id_check(OB12MessageId, message_id)
