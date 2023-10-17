# 消息发送

## 发送时自动选择Bot

在使用saa的主动发送消息功能

```python
async def send_to(
    self: Self@MessageFactory[TMSF@MessageFactory],
    target: PlatformTarget,
    bot: Bot | None = None
) -> Receipt:
    ...
```

时，可以使用`enable_auto_select_bot`函数来开启自动选择Bot功能。
开启后，saa会自动选择一个Bot来发送消息，而不需要手动指定Bot。

```python title="nonebot_plugin_xxx/__init__.py"
from nonebot import require
require("nonebot_plugin_saa")

from nonebot_plugin_saa import enable_auto_select_bot
enable_auto_select_bot()
```

:::caution 调用时机
`enable_auto_select_bot`的作用仅仅是将刷新target与bot的映射缓存的函数注册到 nonebot 的`on_bot_connect`和`on_bot_disconnect`事件中，
并不会直接进行缓存的更新，因此在发送时才调用`enable_auto_select_bot`并不会立即生效。  
正确的做法之一是如同示例一样在插件加载时就调用`enable_auto_select_bot`。
:::

:::info 为什么enable_auto_select_bot不是一个配置项？
启用`enable_auto_select_bot`功能是开发者决定的功能，属于开发者的配置项，因此提供一个函数来开启这个功能。  
在不涉及主动发送消息时，不需要saa自动选择Bot发送，而是直接从会话中提取，
而主动发送消息功能的实现取决于开发者，而非用户。  
再者配置项一般由用户决定，存放在配置文件`.env`中，让开发者保证用户开启这个配置不现实。
:::

:::tip
在所有加载的插件中，只要有一个插件开启了`enable_auto_select_bot`功能，
那么所有插件都会自动开启`enable_auto_select_bot`功能。
:::
