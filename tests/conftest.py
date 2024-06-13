import pytest
import nonebot
from nonebug import NONEBOT_INIT_KWARGS, App
from nonebot.adapters.qq import Adapter as QQAdapter
from nonebot.adapters.red import Adapter as RedAdapter
from nonebot.adapters.dodo import Adapter as DoDoAdapter
from nonebot.adapters.feishu import Adapter as FeishuAdapter
from nonebot.adapters.kritor import Adapter as KritorAdapter
from nonebot.adapters.satori import Adapter as SatoriAdapter
from nonebot.adapters.discord import Adapter as DiscordAdpter
from nonebot.adapters.telegram import Adapter as TelegramAdapter
from nonebot.adapters.onebot.v11 import Adapter as OnebotV11Adapter
from nonebot.adapters.onebot.v12 import Adapter as OnebotV12Adapter


def pytest_configure(config: pytest.Config) -> None:
    config.stash[NONEBOT_INIT_KWARGS] = {"driver": "~fastapi+~websockets+~httpx"}


@pytest.fixture
def app(app: App):
    from nonebot_plugin_saa.registries import PlatformTarget, QQGuildDMSManager

    yield app

    PlatformTarget._deserializer_dict.clear()
    QQGuildDMSManager._cache.clear()


@pytest.fixture(scope="session", autouse=True)
def load_adapters(nonebug_init: None):  # noqa: PT004
    driver = nonebot.get_driver()
    driver.register_adapter(OnebotV11Adapter)
    driver.register_adapter(OnebotV12Adapter)
    driver.register_adapter(TelegramAdapter)
    driver.register_adapter(FeishuAdapter)
    driver.register_adapter(RedAdapter)
    driver.register_adapter(DoDoAdapter)
    driver.register_adapter(QQAdapter)
    driver.register_adapter(SatoriAdapter)
    driver.register_adapter(DiscordAdpter)
    driver.register_adapter(KritorAdapter)
