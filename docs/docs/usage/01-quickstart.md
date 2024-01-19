---
slug: /usage
---

# 快速开始

:::info[开始之前]

在一切之前，默认你已经部署好一个 NoneBot2 的实例，并且已经成功运行。

> 还没有？请参考 [nOneboT的快速上手](https://nonebot.dev/docs/next/quick-start) 章节。

:::

这是一个简单的实例，展示了SAA的基础使用方法

## 安装

在这里将使用 [nb-cli](https://cli.nonebot.dev/) 来安装 SAA 插件

```bash
nb plugin install nonebot-plugin-send-anything-anywhere
```

## 示例

接下来，我们将使用 SAA 来实现一个经典的插件：[`nonebot-plugin-weather`](https://nonebot.dev/docs/next/tutorial/handler)

### 用户查询

我们假设有这样一个需求：用户输入 `天气 <城市>`，机器人将会返回该地的天气信息。

```python
from nonebot.rule import to_me
from nonebot.plugin import on_command

weather = on_command("天气", rule=to_me(), aliases={"weather", "查天气"}, priority=10, block=True)

@weather.handle()
async def get_weather():
    pass  # do something here
```

接着，插件应该去调用一个天气API，获取天气信息，然后将信息发送给用户。

然后需要将文本信息发送给用户，这里我们使用 SAA 插件来实现。

:::tip[别忘了加载插件]

在调用 SAA 插件之前，需要先 `require("nonebot_plugin_saa")`，以确保插件已经被加载。

还需要注意的是, 与安装所用的包名 `nonebot-plugin-send-anything-anywhere` 不同，这里使用的是 **`nonebot_plugin_saa`**。
:::

对于获取到的天气文本信息，需要先使用 `Text` 来包装，然后使用 `send` 来发送。

```python
from nonebot import require, on_command
from nonebot.rule import to_me
from nonebot.adapters import Message
from nonebot.params import CommandArg

require("nonebot_plugin_saa")
from nonebot_plugin_saa import Text

async def weather_api(city: str) -> str:
    response: str = "柳州: 🌦   +14°C"# 能返回文本的天气API
    return response

weather = on_command("天气", rule=to_me(), aliases={"weather", "查天气"}, priority=10, block=True)

@weather.handle()
async def get_weather(args: Message = CommandArg()):
    if location := args.extract_plain_text():
        result = await weather_api(location)
        await Text(result).send()
    else:
        await Text("请输入要查询的地点").finish()
```

可能在 Bot 发送天气消息时，我们希望 Bot 能同时 `@用户`并回复

```python
# ...
@weather.handle()
async def get_weather(args: Message = CommandArg()):
    if location := args.extract_plain_text():
        result = await weather_api(location)
        await Text(result).send(at_sender=True, reply=True)
    else:
        await Text("请输入要查询的地点").finish()
```

这样，当用户输入 `天气 柳州` 时，Bot 将会回复消息，并在消息前 `@用户`

![插件-仅文字](../assets/plugin-only-text.png)

也可以进行图文混排，这个时候，我们需要使用 `Image` 来包装图片，并且使用 `Message` 来组装文本和图片。

```python
from pathlib import Path

assets_path = #资源文件夹路径

# ...
@weather.handle()
async def get_weather(args: Message = CommandArg()):
    if location := args.extract_plain_text():
        result = await weather_api(location)
        await MessageFactory([Text(result), Image(assets_path / "rainy.png")]).send(
            at_sender=True, reply=True
        )
    else:
        await Text("请输入要查询的地点").finish()
```

<!-- ![插件-图文混排](../assets/plugin-text-image.png) #TODO-->

:::info[内置的消息段类型]

上文中，我们使用了 `Text` 和 `Image` 来包装文本和图片，这些都是 SAA 内置的消息段类型。

所有的消息段类型参见 [消息构建](./02-message-build.md) 章节。

:::

### 定时推送

TODO.
