from strenum import StrEnum


class SupportedAdapters(StrEnum):
    onebot_v11 = "OneBot V11"
    onebot_v12 = "OneBot V12"
    kaiheila = "Kaiheila"
    telegram = "Telegram"
    feishu = "Feishu"
    red = "RedProtocol"
    dodo = "DoDo"
    qq = "QQ"
    satori = "Satori"
    discord = "Discord"

    fake = "fake"  # for nonebug


class SupportedPlatform(StrEnum):
    qq_group = "QQ Group"
    qq_private = "QQ Private"
    qq_group_openid = "QQ Group OpenID"
    qq_private_openid = "QQ Private OpenID"
    qq_guild_channel = "QQ Guild Channel"
    qq_guild_direct = "QQ Guild Direct"
    kaiheila_channel = "Kaiheila Channel"
    kaiheila_private = "Kaiheila Private"
    unknown_ob12 = "Unknow Onebot 12 Platform"
    unknown_satori = "Unknown Satori Platform"
    telegram_common = "Telegram Common"
    telegram_forum = "Telegram Forum"
    feishu_private = "Feishu Private"
    feishu_group = "Feishu Group"
    dodo_channel = "DoDo Channel"
    dodo_private = "DoDo Private"
    discord_channel = "Discord Channel"


supported_adapter_names = set(SupportedAdapters._member_map_.values())
