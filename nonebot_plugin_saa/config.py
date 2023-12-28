from nonebot import get_driver
from pydantic import Field, BaseModel


class ScopedConfig(BaseModel):
    use_qqguild_magic_msg_id: bool = Field(
        default=False, description="QQ频道是否使用魔法消息ID发送主动消息"
    )
    """QQ频道是否使用魔法消息ID发送主动消息"""

    qqguild_magic_msg_id: str = Field(default="1000", description="QQ频道魔法消息ID")
    """QQ频道魔法消息ID"""


class Config(BaseModel):
    saa: ScopedConfig = Field(default_factory=ScopedConfig)
    """峯驰物流插件配置"""


plugin_config = Config.parse_obj(get_driver().config).saa
