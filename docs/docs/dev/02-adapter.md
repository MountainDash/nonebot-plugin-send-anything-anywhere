# 添加 Adapter

适配一个新的 adapter 需要完成以下工作：

## 适配 message_id

在 引用/回复 某条消息时，需要使用一个唯一标识来确定某条消息，为此首先需要定义一个 `MessageId`：

```python
class OB11MessageId(MessageId):
    adapter_name: Literal[SupportedAdapters.onebot_v11] = SupportedAdapters.onebot_v11

    message_id: int
```

对于只需要一个字段的大部分 adapter，可以直接把 `MessageId` 定义成上述样子。

并且需要声明如何从 event 中提取出刚才定义的 `MessageId`:

```python
  @register_message_id_getter(MessageEvent)
  def _(event: nonebot.adapters.Event) -> OB11MessageId:
      assert isinstance(event, MessageEvent)
      return OB11MessageId(message_id=event.message_id)
```

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

需要声明如何将**事件**转化为 PlatformTarget，SAA 支持直接注册事件的基类。

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

## 适配 receipt

receipt 是发送消息的收据，我们可以根据这个收据撤回发送的消息。

```python
class OB11Receipt(Receipt):
    message_id: int
    adapter_name: Literal[SupportedAdapters.onebot_v11] = SupportedAdapters.onebot_v11

    # 通过这个函数撤回消息
    async def revoke(self):
        return await cast(BotOB11, self._get_bot()).delete_msg(
            message_id=self.message_id
        )

    # 这个函数需要直接返回调用 adapter.send 所返回的原始内容
    @property
    def raw(self) -> Any:
        return self.message_id
```

## 适配 send（重要）

这个函数完成所有发送的逻辑，它首先需要传入5个参数：

- bot
- msg: MessageFactory，需要发送的内容
- target: PlatformTarget, 需要发送到的目的地
- event: Optional[Event]，触发消息的事件，如果是主动发送消息则为None
- at_sender: bool，需不需要顺带at发送者
- reply: bool, 需不需要以回复消息的形式发送

而且需要返回刚才定义的 Receipt

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
) -> OB11Receipt:
    assert isinstance(bot, BotOB11)
    assert isinstance(target, (TargetQQGroup, TargetQQPrivate))
    if event:
        assert isinstance(event, MessageEvent)
        full_msg = assamble_message_factory(
            msg,
            Mention(event.get_user_id()),
            Reply(OB11MessageId(message_id=event.message_id)),
            at_sender,
            reply,
        )
    else:
        full_msg = msg
    message_to_send = Message()
    for message_segment_factory in full_msg:
        message_segment = await message_segment_factory.build(bot)
        message_to_send += message_segment
    # https://github.com/botuniverse/onebot-11/blob/master/api/public.md#send_msg-%E5%8F%91%E9%80%81%E6%B6%88%E6%81%AF
    res_dict = await bot.send_msg(message=message_to_send, **target.arg_dict(bot))
    message_id = cast(int, res_dict["message_id"])
    return OB11Receipt(bot_id=bot.self_id, message_id=message_id)
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
