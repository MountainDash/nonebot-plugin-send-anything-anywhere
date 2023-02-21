from strenum import StrEnum


class SupportedAdapters(StrEnum):
    onebot_v11 = "OneBot V11"
    onebot_v12 = "OneBot V12"
    qqguild = "QQ Guild"


supported_adapter_names = set(SupportedAdapters._member_map_.values())
