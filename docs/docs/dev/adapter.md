# 添加 Adapter

适配一个新的 adapter 需要完成以下工作：

## 适配 MessageSegmentFactory

需要声明如何将 saa 中的各种 MessageSegmentFactory 转换成这种 adapter 中的 MessageSegment，一般需要手写一个函数来完成转换，并且进行注册。

注册的函数是：`utils.register_ms_adapter`，推荐的注册方法如下：

```python
register_onebot_v11 = partial(register_ms_adapter, SupportedAdapters.onebot_v11)

@register_onebot_v11(Text)
def _text(t: Text) -> MessageSegment:
    return MessageSegment.text(t.data["text"])
```

目前需要支持的 MessageSegmentFactory 包括：

- Text
- Image
- Mention
- Reply

## 适配提取 PlatformTarget

:::caution
确保之前已经添加了对应的 PlatformTarget
:::

需要声明如何将**事件**转化为 PlatformTarget

注册函数是 `utils.register_target_extractor`

```python
@register_target_extractor(PrivateMessageEvent)
def _extract_private_msg_event(event: Event) -> TargetQQPrivate:
    assert isinstance(event, PrivateMessageEvent)
    return TargetQQPrivate(user_id=event.user_id)
```

## 适配 convert_to_arg

需要声明如何将某种 PlatformTarget 转换为调用 `bot.send` 时，向其传入的 kwargs dict
:::note
这是一个解耦的设计，将这部分内容写在`send`中并不影响功能实现
:::

```python
@register_convert_to_arg(adapter, SupportedPlatform.qq_private)
def _gen_private(target: PlatformTarget) -> Dict[str, Any]:
    assert isinstance(target, TargetQQPrivate)
    return {
        "message_type": "private",
        "user_id": target.user_id,
    }
```

## 适配 send（重要）

这个函数完成所有发送的逻辑，它首先需要传入5个参数：

- bot
- msg: MessageFactory，需要发送的内容
- target: PlatformTarget, 需要发送到的目的地
- event: Optional[Event]，触发消息的事件，如果是主动发送消息则为None
- at_sender: bool，需不需要顺带at发送者
- reply: bool, 需不需要以恢复消息的形式发送

需要实现的功能简单来说，是将 msg 在 bot 上发送到 target 去，如果是回复消息的形式，那么根据`at_sender`和`reply`来判断需不需要在回复的消息中顺带 at 发送人，引用原来的消息。

下面是一个例子：

```python
@register_sender(SupportedAdapters.onebot_v11)
async def send(
    bot,
    msg: MessageFactory[MessageSegmentFactory],
    target,
    event,
    at_sender: bool,
    reply: bool,
):
    assert isinstance(bot, BotOB11)
    assert isinstance(target, (TargetQQGroup, TargetQQPrivate))
    if event:
        assert isinstance(event, MessageEvent)
        full_msg = assamble_message_factory(
            msg,
            Mention(event.get_user_id()),
            Reply(event.message_id),
            at_sender,
            reply,
        )
    else:
        full_msg = msg
    message_to_send = Message()
    for message_segment_factory in full_msg:
        message_segment = await message_segment_factory.build(bot)
        message_to_send += message_segment
    await bot.send_msg(message=message_to_send, **target.arg_dict(bot))
```

## 适配聚合发送

TODO

## 适配 list_targets

传入一个 bot，返回这个 bot 能发送到的所有 PlatformTarget

```python
@register_list_targets(SupportedAdapters.onebot_v11)
async def list_targets(bot: Bot) -> List[PlatformTarget]:
    assert isinstance(bot, BotOB11)

    targets = []
    groups = await bot.get_group_list()
    for group in groups:
        group_id = group["group_id"]
        target = TargetQQGroup(group_id=group_id)
        targets.append(target)

    # 获取好友列表
    users = await bot.get_friend_list()
    for user in users:
        user_id = user["user_id"]
        target = TargetQQPrivate(user_id=user_id)
        targets.append(target)

    return targets
```
