from strenum import StrEnum


class SupportedAdapters(StrEnum):
    onebot_v11 = "OneBot V11"
    onebot_v12 = "OneBot V12"
    qqguild = "QQ Guild"


class SupportedPlatform(StrEnum):
    qq_group = "QQ Group"
    qq_private = "QQ Private"
    qq_guild_channel = "QQ Guild Channel"
    qq_guild_direct = "QQ Guild Direct"
    unknown_ob12 = "Unknow Onebot 12 Platform"


supported_adapter_names = set(SupportedAdapters._member_map_.values())
