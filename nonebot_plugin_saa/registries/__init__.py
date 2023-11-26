from .receipt import Receipt as Receipt
from .message_id import MessageId as MessageId
from .message_id import SaaMessageId as SaaMessageId
from .message_id import get_message_id as get_message_id
from .platform_send_target import SaaTarget as SaaTarget
from .platform_send_target import get_target as get_target
from .platform_send_target import sender_map as sender_map
from .platform_send_target import TargetQQGroup as TargetQQGroup
from .platform_send_target import TargetQQGroupOpenId as TargetQQGroupOpenId
from .platform_send_target import PlatformTarget as PlatformTarget
from .platform_send_target import extract_target as extract_target
from .platform_send_target import TargetQQPrivate as TargetQQPrivate
from .platform_send_target import TargetQQPrivateOpenId as TargetQQPrivateOpenId
from .platform_send_target import register_sender as register_sender
from .platform_send_target import TargetOB12Unknow as TargetOB12Unknow
from .platform_send_target import QQGuildDMSManager as QQGuildDMSManager
from .platform_send_target import TargetDoDoChannel as TargetDoDoChannel
from .platform_send_target import TargetDoDoPrivate as TargetDoDoPrivate
from .platform_send_target import TargetFeishuGroup as TargetFeishuGroup
from .platform_send_target import TargetFeishuPrivate as TargetFeishuPrivate
from .platform_send_target import TargetQQGuildDirect as TargetQQGuildDirect
from .platform_send_target import TargetTelegramForum as TargetTelegramForum
from .platform_send_target import TargetQQGuildChannel as TargetQQGuildChannel
from .platform_send_target import TargetTelegramCommon as TargetTelegramCommon
from .platform_send_target import register_qqguild_dms as register_qqguild_dms
from .message_id import register_message_id_getter as register_message_id_getter
from .platform_send_target import TargetKaiheilaChannel as TargetKaiheilaChannel
from .platform_send_target import TargetKaiheilaPrivate as TargetKaiheilaPrivate
from .platform_send_target import register_convert_to_arg as register_convert_to_arg
from .platform_send_target import register_target_extractor as register_target_extractor
from .platform_send_target import (
    AllSupportedPlatformTarget as AllSupportedPlatformTarget,
)
