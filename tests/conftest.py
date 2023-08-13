import nonebot
import pytest
from nonebot.adapters.discord import Adapter as DiscordAdpter
from nonebot.adapters.feishu import Adapter as FeishuAdapter
from nonebot.adapters.onebot.v11 import Adapter as OnebotV11Adapter
from nonebot.adapters.onebot.v12 import Adapter as OnebotV12Adapter
from nonebot.adapters.qqguild import Adapter as QQGuildAdapter
from nonebot.adapters.telegram import Adapter as TelegramAdapter
from nonebug import NONEBOT_INIT_KWARGS, App


def pytest_configure(config: pytest.Config) -> None:
    config.stash[NONEBOT_INIT_KWARGS] = {"driver": "~fastapi+~websockets"}


@pytest.fixture
def app(app: App):
    from nonebot_plugin_saa.utils.platform_send_target import (
        PlatformTarget,
        QQGuildDMSManager,
    )

    yield app

    PlatformTarget._deseriazer_map.clear()
    QQGuildDMSManager._cache.clear()


@pytest.fixture(scope="session", autouse=True)
def load_adapters(nonebug_init: None):
    driver = nonebot.get_driver()
    driver.register_adapter(OnebotV11Adapter)
    driver.register_adapter(OnebotV12Adapter)
    driver.register_adapter(QQGuildAdapter)
    driver.register_adapter(TelegramAdapter)
    driver.register_adapter(FeishuAdapter)
    driver.register_adapter(DiscordAdpter)
