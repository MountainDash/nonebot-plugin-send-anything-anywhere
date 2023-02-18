<div align="center">

~logo征集中，假装有图片~

# Nonebot Plugin<br>Send Anything Anywhere

你只管业务实现，把发送交给我们

![GitHub Workflow Status](https://img.shields.io/github/actions/workflow/status/felinae98/nonebot-plugin-send-anything-anywhere/test.yml)
![Codecov](https://img.shields.io/codecov/c/github/felinae98/nonebot-plugin-send-anything-anywhere)

</div>

这个插件可以做什么

- 为常见的消息类型提供抽象类，自适应转换成对应 adapter 的消息
- 提供一套统一的，符合直觉的发送接口（规划中）
- 为复杂的消息提供易用的生成接口（规划中）

本插件通过传入 bot 的类型来自适应生成对应 bot adapter 所使用的 Message

## 安装

TODO

## 支持的 adapter

- [x] OneBot v11
- [x] OneBot v12

## 支持的消息类型

- [x] 文字（全平台）
- [x] 图片（全平台）
- [x] at（全平台)
- [x] 回复（全平台）

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
from nonebot_plugin_send_anything_anywhere import Image, Text, MessageFactory

pic_matcher = nonebot.on_command('发送图片')

pic_matcher.handle()
async def _handle_v12(bot: Bot, event: Union[V12MessageEvent, V11MessageEvent]):
    pic_content = ...
    msg_builder = MessageFactory([
        Image(pic_content), Text("这是你要的图片")
    ])
    # or msg_builder = Image(pic_content) + Text("这是你要的图片")
    msg = await msg_builder.build(bot)
    await pic_matcher.finish(msg)
```

## 类似项目

- [nonebot-plugin-all4one](https://github.com/nonepkg/nonebot-plugin-all4one) 解决了类似的问题，但是用了不同路径
- [nonebot-plugin-params](https://github.com/iyume/nonebot-plugin-params) 通过 Rule 定制订阅的平台，与本插件联合使用也许会有奇效

## License

TODO
