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

```python
from nonebot_plugin_saa import enable_auto_select_bot

enable_auto_select_bot()
```

:::info 为什么enable_auto_select_bot不是一个配置项？

启用`enable_auto_select_bot`功能是属于开发者决定的功能，
在不涉及主动发送消息时，enable_auto_select_bot没有必要开启，
这些都由开发者决定，而不是用户。

配置项一般由用户决定，存放在配置文件`.env`中，
让开发者保证用户开启了这个配置不现实。

:::

:::tip

在所有加载的插件中，只要有一个插件开启了`enable_auto_select_bot`功能，
那么所有插件都会自动开启`enable_auto_select_bot`功能。

:::
