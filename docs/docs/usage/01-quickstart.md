---
slug: /usage
---

# 快速开始

nonebot-plugin-send-anything-anywhere （以下简称 saa），是一个用于适配多 adapter 的插件，
用户可以通过构建统一抽象的消息，saa 将消息自动转换成各个平台的 Message，并且发送消息。

## 安装

- 使用 nb-cli 安装  
  `nb plugin install nonebot-plugin-send-anything-anywhere`
- 使用 poetry 安装  
  `poetry add nonebot-plugin-send-anything-anywhere`
- 使用 pip 安装  
  `pip install nonebot-plugin-send-anything-anywhere`

## 基本使用

### 在 handler 中回复消息的情况

```python
@matcher.handle()
async def handle(_: SaaTarget): # 可以保证只有 saa 支持的消息才会触发这个 handler
    # 直接调用 MessageFactory.send() 在 handler 中回复消息
    await MessageFactory("你好").send(reply=True, at_sender=True)
    await MessageFactory("需要回复的内容").finish()
```

- 关于 `MessageFactory` 的构建，请查阅[消息构建](./02-message-build.md)
- 关于发送相关的内容，请查阅[发送](./03-send.md)
- 如果想定制转换后的消息，请查阅[自定义消息](./04-custom.md)

### 主动发送的情况

```python
from nonebot_plugin_saa import TargetQQGroup

# 发送目标为 QQ 号 10000, 以私聊形式发送
target = TargetQQGroup(group_id=2233)
await MessageFactory("早上好").send_to(target, bot)
```

- 如果想要自动选择发送的机器人，请查阅[发送](./03-send.md)
