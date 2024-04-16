from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from nonebot_plugin_saa.registries.message_id import MessageId


class AdapterNotInstalled(Exception):
    def __init__(self, adapter_name: str) -> None:
        message = f'adapter "{adapter_name}" not installed, please install first'
        super().__init__(self, message)


class AdapterNotSupported(Exception):
    def __init__(self, adapter_name: str) -> None:
        message = f'adapter "{adapter_name}" not supported'
        super().__init__(self, message)


class NoBotFound(RuntimeError):
    pass


class FallbackToDefault(Exception):
    pass


class UnexpectedMessageIdType(Exception):
    def __init__(
        self, expected_type: "type[MessageId]", message_id: "MessageId"
    ) -> None:
        super().__init__(
            self,
            f"expected message_id type {expected_type.__name__}, "
            f"got {message_id.__class__.__name__}",
        )
