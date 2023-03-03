from typing import Literal


def test_register_deserializer():
    from nonebot_plugin_saa import SupportedAdapters
    from nonebot_plugin_saa.utils.send_target import AbstractSendTarget, deserialize

    class MySendTarget(AbstractSendTarget):
        adapter_type: Literal[
            SupportedAdapters.onebot_v11
        ] = SupportedAdapters.onebot_v11
        my_field: int

    send_target = MySendTarget(my_field=123)
    serialized_target = send_target.json()
    deserialized_target = deserialize(serialized_target)

    assert isinstance(deserialized_target, MySendTarget)
    assert deserialized_target == send_target


def test_export_args():
    from nonebot_plugin_saa.adapters.onebot_v11 import SendTargetOneBot11

    target = SendTargetOneBot11(group_id=31415, message_type="private")
    assert target.arg_dict() == {"group_id": 31415, "message_type": "private"}
