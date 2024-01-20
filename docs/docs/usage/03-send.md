# 消息发送

SAA 的 `MessageSegmentFactory`、`MessageFactory`、`AggregatedMessageFactory` 都实现了消息的发送功能。

## 被动发送

被动发送是指用户方触发消息发送，例如用户发送一条消息，然后Bot进行回复。

对于这个场景，可以直接使用 `send` 方法，saa会自动提取会话中的 PlatformTarget 和 Bot 进行发送。

```python
cmd = on_command("repeat", rule=to_me())

@cmd.handle()
async def _(args: Message = CommandArg()):
    await Text(args.extract_plain_text()).send()
```

## 主动发送

主动发送是指 Bot 方在没有用户触发的情况下发送消息，例如每天早八的早安问候 ~(?)~。

显然在这个场景下，我们无法从会话中提取 PlatformTarget 和 Bot，因此需要使用 `send_to` 方法，并手动指定参数。

```python
from nonebot import get_bot

@scheduler.scheduled_job("cron", hour=8, id="morning_greeting")
async def morning_greeting():
    await Text("博士，你今天有早八，还不能休息哦").send_to(
        target=PlatformTarget.deserialize(await get_target_from_db(...)),
        bot=get_bot()
    )
```

:::info

可以发现其实 `send_to` 方法允许不提供 bot参数，只提供 PlatformTarget，这会让SAA自动按照 PlatformTarget 的具体实例按照一定的规则选择Bot进行发送。

但是启用这个功能需要一定的条件，参见 [自动选择Bot](#发送时自动选择bot)

:::

## PlatformTarget

PlatformTarget 是 SAA 内置的平台目标类型，用于标识消息需要发送到的目的地。

### SaaTarget

SAA 提供了一个便捷的依赖注入来获取 PlatformTarget，即 **`SaaTarget`**

```python
from nonebot_plugin_saa import SaaTarget

cmd = on_command("repeat", rule=to_me())

@cmd.handle()
async def _(target: SaaTarget, args: Message = CommandArg()):
    ...
```

也可以使用 `get_target` 函数，传入 `event` 和 `bot` 参数来提取 PlatformTarget。

这也是 SaaTarget 的内部实现。

### 可用的子类

SAA 内置了一些常用的 PlatformTarget 子类，可以直接使用。

基于 SAA 的设计，某些 PlatformTarget 可以在 SAA 适配的 Adapter 之间通用，例如 `TargetQQGroup` 与 `TargetQQPrivate` 可以在 OnebotV11、OnebotV12、Red 之间通用。

所有可用的 PlatformTarget 子类如下：

- TargetQQGroup
- TargetQQPrivate
- TargetQQGroupOpenId
- TargetQQPrivateOpenId
- TargetQQGuildChannel
- TargetQQGuildDirect
- TargetKaiheilaPrivate
- TargetKaiheilaChannel
- TargetOB12Unknow
- TargetTelegramCommon
- TargetTelegramForum
- TargetFeishuPrivate
- TargetFeishuGroup
- TargetDoDoChannel
- TargetDoDoPrivate

以及一个总的类型 `AllSupportedPlatformTarget`，用于标识所有支持的 PlatformTarget。

### 序列化与反序列化

PlatformTarget 提供了 `dict` 和 `deserialize` 方法，用于序列化和反序列化 PlatformTarget。

这对于将 PlatformTarget 存储到数据库中是非常有用的。

```python
pt = TargetQQGroup(group_id=123456789)
pt_dict = pt.dict()
pt_deserialized = PlatformTarget.deserialize(pt_dict)

assert pt == pt_deserialized
```

:::warning[可反序列化范围]

PlatformTarget 的反序列化方法 `deserialize` 仅支持上述 AllSupportedPlatformTarget 中的子类。

:::

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

在插件加载时调用`enable_auto_select_bot`函数即可开启这个功能。

```python title="nonebot_plugin_xxx/__init__.py"
from nonebot import require
require("nonebot_plugin_saa")

from nonebot_plugin_saa import enable_auto_select_bot
enable_auto_select_bot()
```

:::warning[调用时机]
`enable_auto_select_bot`的作用仅仅是将刷新target与bot的映射缓存的函数注册到 nonebot 的`on_bot_connect`和`on_bot_disconnect`事件中，
并不会直接进行缓存的更新，因此在发送时才调用`enable_auto_select_bot`并不会立即生效。  
正确的做法之一是如同示例一样在插件加载时就调用`enable_auto_select_bot`。
:::

:::info[为什么enable_auto_select_bot不是一个配置项？]
启用`enable_auto_select_bot`功能是开发者决定的功能，属于开发者的配置项，因此提供一个函数来开启这个功能。  
在不涉及主动发送消息时，不需要saa自动选择Bot发送，而是直接从会话中提取，
而主动发送消息功能的实现取决于开发者，而非用户。  
再者配置项一般由用户决定，存放在配置文件`.env`中，让开发者保证用户开启这个配置不现实。
:::

:::tip
在所有加载的插件中，只要有一个插件开启了`enable_auto_select_bot`功能，
那么所有插件都会自动开启`enable_auto_select_bot`功能。
:::
