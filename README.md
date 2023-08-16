<div align="center">

~logo征集中，假装有图片~

# Nonebot Plugin<br>Send Anything Anywhere

你只管业务实现，把发送交给我们

![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/felinae98/nonebot-plugin-send-anything-anywhere/test.yml)
![Codecov](https://img.shields.io/codecov/c/github/felinae98/nonebot-plugin-send-anything-anywhere)
![PyPI - Python Version](https://img.shields.io/pypi/pyversions/nonebot-plugin-send-anything-anywhere)
![PyPI](https://img.shields.io/pypi/v/nonebot-plugin-send-anything-anywhere)
![GitHub](https://img.shields.io/github/license/felinae98/nonebot-plugin-send-anything-anywhere)

</div>

这个插件可以做什么

- 为常见的消息类型提供抽象类，自适应转换成对应 adapter 的消息
- 提供一套统一的，符合直觉的发送接口
- 为复杂的消息提供易用的生成接口（规划中）

本插件通过传入 bot 的类型来自适应生成对应 bot adapter 所使用的 Message

## 安装

- 使用 nb-cli 安装  
  `nb plugin install nonebot-plugin-send-anything-anywhere`
- 使用 poetry 安装  
  `poetry add nonebot-plugin-send-anything-anywhere`
- 使用 pip 安装  
  `pip install nonebot-plugin-send-anything-anywhere`

## 使用

在 handler 中回复消息的情况：

```python
@matcher.handle()
async def handle(event: MessageEvent):
  # 直接调用 MessageFactory.send() 在 handler 中回复消息
  receipt = await MessageFactory("你好").send(reply=True, at_sender=True)
  receipt = await MessageFactory("需要回复的内容").finish()
```

主动发送的情况：

```python
from nonebot_plugin_saa import TargetQQGroup

# 发送目标为 QQ 号 10000, 以私聊形式发送
target = TargetQQGroup(group_id=2233)
receipt = await MessageFactory("早上好").send_to(target)
```

从消息事件中提取发送目标:

```python
from nonebot_plugin_saa import extract_target, get_target


@matcher.handle()
async def handle(event: MessageEvent):
  target = extract_target(event)


@matcher.handle()
async def handle(target: PlatformTarget = Depends(get_target)):
  ...
```

发送目标的序列化与反序列化:

```python
from nonebot_plugin_saa import PlatformTarget, TargetQQPrivate

target = TargetQQPrivate(user_id=112233)
serialized_target = target.json()
deserialized_target = PlatformTarget.deserialize(serialized_target)
assert deserialized_target == target
```

返回数据的使用和序列化与反序列化

```python
from nonebot_plugin_saa import (
  MessageFactory,
  Text,
  Image,
)

receipt = await MessageFactory([Text("2333"), Image(img1, name="1.png")]).send()
# 原始的返回数据(并不是所有适配器均有这个值,可能为None)
print(receipt.sent_msg)
# 原始的返回数据(不可能为None,如果无sent_msg则直接返回message_id)
print(receipt.raw)
# 发出去的消息的id(在相应平台具有唯一性)
print(receipt.message_id)

# 如果可以编辑,编辑这个信息
if receipt.edit_able:
  await receipt.edit(
    [Text("3222"), Image(img2, "2.png")]
  )

# 撤回这条消息
await receipt.revoke()

# 序列化
data = receipt.json()
# 反序列化
receipt_ = Receipt.deserialize(data)

```

## 支持情况

✅:支持 ✖️:支持不了 🚧:等待适配

### 支持的 adapter

| OneBot v11 | OneBot v12 | QQ Guild | Kaiheila | Telegram | Feishu | Discord |
|:----------:|:----------:|:--------:|:--------:|:--------:|:------:|:-------:|
|     ✅      |     ✅      |    ✅     |    ✅     |    ✅     |   ✅    |    ✅    |

### 支持的消息类型

|    | OneBot v11 | OneBot v12 | QQ Guild | 开黑啦 | Telegram | Feishu | Discord |
|:--:|:----------:|:----------:|:--------:|:---:|:--------:|:------:|:-------:|
| 文字 |     ✅      |     ✅      |    ✅     |  ✅  |    ✅     |   ✅    |    ✅    |
| 图片 |     ✅      |     ✅      |    ✅     |  ✅  |    ✅     |   ✅    |    ✅    |
| at |     ✅      |     ✅      |    ✅     |  ✅  |    ✅     |   ✅    |    ✅    |
| 回复 |     ✅      |     ✅      |    ✅     |  ✅  |    ✅     |   ✅    |    ✅    |

### 支持的发送目标

|                  | OneBot v11 | OneBot v12 | QQ Guild | Kaiheila | Telegram | Feishu | Discord |
|:----------------:|:----------:|:----------:|:--------:|:--------:|:--------:|:------:|:-------:|
|       QQ 群       |     ✅      |     ✅      |          |          |          |        |         |
|      QQ 私聊       |     ✅      |     ✅      |          |          |          |        |         |
|    QQ 频道子频道消息    |            |     ✅      |    ✅     |          |          |        |         |
|     QQ 频道私聊      |            |     ✅      |    ✅     |          |          |        |         |
|     开黑啦私聊/频道     |            |            |          |    ✅     |          |        |         |
| Telegram 普通对话/频道 |            |            |          |          |    ✅     |        |         |
|     飞书私聊/群聊      |            |            |          |          |          |   ✅    |         |
|   Discord频道/私聊   |            |            |          |          |          |        |    ✅    |

注：对于使用 Onebot v12，但是没有专门适配的发送目标，使用了 TargetOB12Unknow 来保证其可以正常使用

### 支持的返回数据操作

|    | OneBot v11 | OneBot v12 | QQ Guild | Kaiheila | Telegram | Feishu | Discord |
|:--:|:----------:|:----------:|:--------:|:--------:|:--------:|:------:|:-------:|
| 撤回 |     ✅      |     ✅      |    ✅     |    ✅     |    ✅     |   ✅    |    ✅    |
| 编辑 |     ✖️     |     ✖️     |    ✖️    |    ✅     |    ✅     |   ✅    |    ✅    |

注: 
1. 对于telegram的编辑消息,受限于Tg的消息形式,纯文本仅能编辑为纯文本,文本和图片混合仅能编辑为文本和图片混合,并且编辑后图片的数量能减不能增
2. 对于feishu的编辑消息,不能改变reply的状态,并且一条消息只能编辑20次
## 问题与例子

因为在现在的 Nonebot 插件开发中，消息的构建和发送是和 adapter 高度耦合的，这导致一个插件要适配不同的 adapter 是困难的

before:

```python
from nonebot.adapters.onebot.v11.event import MessageEvent as V11MessageEvent
from nonebot.adapters.onebot.v11.message import MessageSegment as V11MessageSegment
from nonebot.adapters.onebot.v12.event import MessageEvent as V12MessageEvent
from nonebot.adapters.onebot.v12.message import MessageSegment as V12MessageSegment
from nonebot.adapters.onebot.v12.bot import Bot as V12Bot

pic_matcher = nonebot.on_command('发送图片')

pic_matcher.handle()


async def _handle_v11(event: V11MessageEvent):
  pic_content = ...
  msg = V11MessageSegment.image(pic_content) + V11MessageSegment.text("这是你要的图片")
  await pic_matcher.finish(msg)


pic_matcher.handle()


async def _handle_v12(bot: V12Bot, event: V12MessageEvent):
  pic_content = ...
  pic_file = await bot.upload_file(type='data', name='image', data=pic_content)
  msg = V12MessageSegment.image(pic_file['file_id']) + V12MessageSegment.text("这是你要的图片")
  await pic_matcher.finish(msg)
```

现在只需要:

```python
from nonebot.adapters.onebot.v11.event import MessageEvent as V11MessageEvent
from nonebot.adapters.onebot.v12.event import MessageEvent as V12MessageEvent
from nonebot.internal.adapter.bot import Bot
from nonebot_plugin_saa import Image, Text, MessageFactory

pic_matcher = nonebot.on_command('发送图片')

pic_matcher.handle()


async def _handle_v12(bot: Bot, event: Union[V12MessageEvent, V11MessageEvent]):
  pic_content = ...
  msg_builder = MessageFactory([
    Image(pic_content), Text("这是你要的图片")
  ])
  # or msg_builder = Image(pic_content) + Text("这是你要的图片")
  await msg_builder.send()
  await pic_matcher.finish()
```

## 类似项目

- [nonebot-plugin-all4one](https://github.com/nonepkg/nonebot-plugin-all4one) 解决了类似的问题，但是用了不同路径
- [nonebot-plugin-params](https://github.com/iyume/nonebot-plugin-params) 通过 Rule 定制订阅的平台，与本插件联合使用也许会有奇效

## License

MIT
