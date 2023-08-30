async def test_deserialize_receipt():
    from nonebot_plugin_saa.utils import Receipt, SupportedAdapters

    data = {
        "bot_id": "123",
        "message_id": 1238771,
        "adapter_name": SupportedAdapters.onebot_v11,
    }
    assert type(Receipt.deserialize(data)).__name__ == "OB11Receipt"
