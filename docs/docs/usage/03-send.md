# 消息发送

SAA 的 `MessageSegmentFactory`、`MessageFactory`、`AggregatedMessageFactory` 都实现了消息的发送功能。

## 被动发送

被动发送是指用户方触发消息发送，例如用户发送一条消息，然后 Bot 进行回复。

对于这个场景，可以直接使用 `send` 方法，saa会自动提取会话中的 PlatformTarget 和 Bot 进行发送。

```python
cmd = on_command("say", rule=to_me())

@cmd.handle()
async def _(args: Message = CommandArg()):
    await Text(args.extract_plain_text()).send()
```

`send` 方法提供了两个参数，`reply` 和 `at_sender`

当 `reply` 为 `True` 时，发送的消息会自动回复用户的消息。

当 `at_sender` 为 `True` 时，发送的消息会在消息前 `@用户`。

## 主动发送

主动发送是指 Bot 方在没有用户触发的情况下发送消息，例如每天早八的早安问候 ~(?)~。

显然这个场景并不在会话中，无从提取 PlatformTarget 和 Bot，因此需要使用 `send_to` 方法，并手动指定需要发送到的 PlatformTarget 和 Bot。

```python
from nonebot import get_bot

@scheduler.scheduled_job("cron", hour=8, id="morning_greeting")
async def morning_greeting():
    await Text("博士，你今天有早八，还不能休息哦").send_to(
        # 在这里，假设存在一个函数 get_target_from_db 来从数据库中获取 PlatformTarget 的序列化结果
        target=PlatformTarget.deserialize(await get_target_from_db(...)),
        bot=get_bot()
    )
```

`send_to` 方法并不提供 `reply` 和 `at_sender` 参数，因为这些参数只有在会话中才有意义。想要在主动发送时使用这些消息段，需要手动构造。

:::info

其实 `send_to` 方法允许不提供 bot 参数，只提供 PlatformTarget，这会让 SAA 自动按照 PlatformTarget 的具体实例根据一定的规则选择 Bot 进行发送。

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

:::warning[什么时候需要传入bot参数]

`get_target` 函数及其更内部的 `extract_target` 函数使用时一般不需要传入 bot 参数。

bot 参数主要用于那些混入了 [BotSpecifier](#botspecifier) 的 PlatformTarget，主要是 OpenID 相关的 PlatformTarget。

:::

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

### BotSpecifier

BotSpecifier 是一个 Mixin 类，用于指定 PlatformTarget 与 Bot 的绑定关系。

混入了 BotSpecifier 的 PlatformTarget 与一个特定的 Bot 关联，因为只有这个 Bot 才能正确使用这个 PlatformTarget。

:::note[实际案例]

QQ开放平台的 [OpenID 机制](https://bot.q.qq.com/wiki/develop/api-v2/dev-prepare/unique-id.html)就是如此，不同 Bot 对同一个目标，所获得的 ID 是不同的，因此需要 BotSpecifier 来指定这个 OpenID 与 Bot 的绑定关系。

:::

## 发送时自动选择Bot

在使用 SAA 的主动发送消息功能

```python
async def send_to(
    self: Self@MessageFactory[TMSF@MessageFactory],
    target: PlatformTarget,
    bot: Bot | None = None
) -> Receipt:
    ...
```

时，可以使用 `enable_auto_select_bot` 函数来开启自动选择 Bot 功能。
开启后，SAA 会自动选择一个 Bot 来发送消息，而不需要手动指定 Bot。

在插件加载时调用 `enable_auto_select_bot` 函数即可开启这个功能。

```python title="nonebot_plugin_xxx/__init__.py"
from nonebot import require
require("nonebot_plugin_saa")

from nonebot_plugin_saa import enable_auto_select_bot
enable_auto_select_bot()
```

:::warning[调用时机]
`enable_auto_select_bot` 的作用仅仅是将刷新 target 与 bot 的映射缓存的函数注册到 nonebot 的 `on_bot_connect` 和 `on_bot_disconnect` 事件中，
并不会直接进行缓存的更新，因此在发送时才调用 `enable_auto_select_bot` 并不会立即生效。  
正确的做法之一是如同示例一样在插件加载时就调用 `enable_auto_select_bot` 。
:::

:::info[为什么enable_auto_select_bot不是一个配置项？]
启用 `enable_auto_select_bot` 功能是开发者决定的功能，属于开发者的配置项，因此提供一个函数来开启这个功能。  
在不涉及主动发送消息时，不需要 SAA 自动选择 Bot 发送，而是直接从会话中提取，
而主动发送消息功能的实现取决于开发者，而非用户。  
再者配置项一般由用户决定，存放在配置文件 `.env` 中，让开发者保证用户开启这个配置不现实。
:::

:::tip
在所有加载的插件中，只要有一个插件开启了 `enable_auto_select_bot` 功能，
那么所有插件都会自动开启 `enable_auto_select_bot` 功能。
:::
