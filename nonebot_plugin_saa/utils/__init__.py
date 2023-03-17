from .helpers import extract_adapter_type
from .exceptions import AdapterNotInstalled, AdapterNotSupported
from .const import SupportedAdapters, SupportedPlatform, supported_adapter_names
from .types import (
    BuildFunc,
    MessageFactory,
    CustomBuildFunc,
    MessageSegmentFactory,
    AggregatedMessageFactory,
    do_build,
    do_build_custom,
    register_ms_adapter,
    assamble_message_factory,
)
from .platform_send_target import (
    TargetQQGroup,
    PlatformTarget,
    TargetQQPrivate,
    TargetOB12Unknow,
    TargetQQGuildDirect,
    TargetQQGuildChannel,
    extract_target,
    register_sender,
    register_convert_to_arg,
    register_target_extractor,
)

__all__ = [
    "SupportedAdapters",
    "SupportedPlatform",
    "supported_adapter_names",
    "AdapterNotInstalled",
    "AdapterNotSupported",
    "MessageSegmentFactory",
    "MessageFactory",
    "AggregatedMessageFactory",
    "register_ms_adapter",
    "extract_adapter_type",
    "BuildFunc",
    "CustomBuildFunc",
    "do_build",
    "do_build_custom",
    "extract_target",
    "register_target_extractor",
    "register_sender",
    "assamble_message_factory",
    # PlatformTarget
    "register_convert_to_arg",
    "register_target_extractor",
    "TargetQQGroup",
    "TargetQQPrivate",
    "TargetQQGuildChannel",
    "TargetQQGuildDirect",
    "TargetOB12Unknow",
    "PlatformTarget",
]
