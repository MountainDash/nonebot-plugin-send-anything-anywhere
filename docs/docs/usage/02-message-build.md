# 消息构建

## 内置的消息段类型(MessageSegmentFactory)

SAA 内置的消息段类型有：

- `Text`：文本消息段
- `Image`：图片消息段
- `Reply`：回复消息段
- `Mention`：提及消息段
- `MentionAll`：提及全体消息段

上述消息段类型都是 `MessageSegmentFactory` 的子类。

`MessageSegmentFactory` 将数据保存在其 `data: dict[str, Any]` 字段中。

### Text

`Text` 用于包装文本消息(str)。

```python
from nonebot_plugin_saa import Text

text = Text("Hello World!")
```

### Image

`Image` 用于包装图片消息，可以使用 `Image` 来包装的图片类型有：

- `str`：图片路径，以 `http://` 或 `https://` 开头的链接，或者以 `file://` 开头的本地文件路径
- `Path`：图片路径，`pathlib.Path` 类型
- `bytes`：图片二进制数据
- `io.BytesIO`：图片二进制数据，`io.BytesIO` 类型

```python
from io import BytesIO
from pathlib import Path
from nonebot_plugin_saa import Image

image0 = Image("http://example.com/image.png")
image1 = Image("file:///home/user/image.png")
image2 = Image(Path("/home/user/image.png"))
image3 = Image(b"image binary data")
image4 = Image(BytesIO(b"image binary data"))
```

### Reply

`Reply` 用于包装回复消息，`Reply` 消息段只接受 `MessageId` 进行构建。

:::tip[MessageId?]

`MessageId` 是 SAA 内置的消息 ID 类型，SAA使用其来标识消息。

:::

对于用户对话中的消息，我们并不需要手动构建 `Reply` 消息段，而是可以直接使用 `reply` 参数来构建。

```python
await Text("Hello World!").send(reply=True)
```

如果想要回复 Bot 发送的消息，可以使用 消息回执(`Receipt`) 来构建 `Reply` 消息段。

:::tip[Receipt?]

SAA 发送消息时，会返回一个 `Receipt` 对象，可以使用 `Receipt.extract_message_id()` 来获取消息 ID。

:::

```python
receipt = await Text("Hello World!").send()

reply = Reply(receipt.extract_message_id())
```

:::warning[直接使用 MessageId?]

如果想要直接使用 `MessageId` 来构建 `Reply` 消息段是比较麻烦的，因为我们需要手动构建 `MessageId`，并且需要知道该适配器需要的 `MessageId` 格式。

这个行为会导致严重的平台特化现象，因此**不推荐**使用。

:::

### Mention

`Mention` 用于包装提及消息，`Mention` 消息段只接受 `user_id: str` 进行构建。

对于用户对话中的消息，我们并不需要手动构建 `Mention` 消息段，而是可以直接使用 `at_sender` 参数来构建。

```python
await Text("Hello World!").send(at_sender=True)
```

如果想要在构建的消息的特定位置插入提及消息，可以使用 `Mention` 消息段。

```python
mention = Mention("123456789")
```

:::info[如何获取 user_id?]

SAA 并不提供 user_id 的获取方法，因此需要自行获取。

```python
from nonebot.adapters import Event

@matcher.handle()
async def handle(event: Event):
    user_id = event.get_user_id()
    ...
```

:::

### MentionAll

`MentionAll` 用于包装提及全体消息，可以认为是 `Mention` 的特例。
其中某些 Adapter 通过在 `Mention` 中使用特别的 `user_id` 来实现提及全体消息（比如飞书、Onebot V11），另一些 Adapter 则通过独立的 `MentionAll` 来实现（比如 Onebot V12、Satori）。

因此为了统一提及全体消息的行为，SAA 提供了 `MentionAll` 消息段。

```python
from nonebot_plugin_saa import MentionAll

mention_all = MentionAll()
```

:::warning[不支持提及全体消息时的行为]
目前并不是所有 Adapter 都支持提及全体消息，如果将提及全体消息发送给不支持的 Adapter，将会进行 **fallback**。

fallback 的默认行为是将 `MentionAll` 替换为 `Text`，用文本消息 `@全体成员` 替代。（取决于 Adapter 的适配实现）。

如果在 `MentionAll` 消息段中指定了 `fallback` 参数，将会使用该参数**原样**作为 fallback 的文本。

有时可能对不同的 Adapter 需要不同的 fallback 文本，这时可以使用 `MentionAll` 实例的`set_specific_fallback` 方法来设置特定适配器的 fallback 文本。

fallback文本的应用优先级为：`set_specific_fallback` > `fallback` > 默认fallback文本。
:::

## MessageId

`MessageId` 是 SAA 内置的消息 ID 类型，SAA 使用其来标识消息。

`MessageId` 由 `adapter_name: str` 和 一系列平台各异的字段组成。

`MessageId` 一般会被各个SAA适配的Adapter的 `XxxMessageId` 子类所继承。

:::note

大多数 SAA 适配的 Adapter 实现的 MessageId 子类都只有额外的一个`message_id`字段，用于保存平台的消息 ID，但其类型可能不同(str/int)。

但对于个别适配器，其 `MessageId` 子类可能会有更多的字段，如 Red。

:::

## Receipt

`Receipt` 是 SAA 内置的消息回执类型，用于标识消息的发送结果。

`Receipt` 一般会被各个 SAA 适配的 Adapter 的 `XxxReceipt` 子类所继承。

`Receipt` 提供了以下通用方法：

- `Receipt.extract_message_id()`：从回执中提取 [`MessageId`](#messageid)
- `Receipt.revoke()`: 撤回该回执对应的发送消息
- `Receipt.raw`：原始回执数据

对于各个具体子类，其可能会提供更多的方法。

例如 DoDo, 其 `DoDoReceipt` 提供了 `edit`, `pin` 方法来编辑消息和置顶消息。

## 内置的消息类型(MessageFactory)

MessageFactory 是 MessageSegmentFactory 的集合，用于将各个消息段组合为一条消息

目前 SAA 内置的消息类型有且仅有 `MessageFactory`。

```python
from nonebot_plugin_saa import Text, Image, MessageFactory

mf = MessageFactory([Text("Hello World!"), Image("http://example.com/image.png")])
```

与 Nonebot 原生的 Message 类似，`MessageFactory` 也提供了若干工具方法提供对消息段的操作，这里不再赘述。

:::info[会话控制]

MessageFactory 与 MessageSegmentFactory 均提供了 Nonebot [会话控制](https://nonebot.dev/docs/appendices/session-control)所需的方法。

:::

## 内置的聚合消息类型(AggregatedMessageFactory)

AggregatedMessageFactory 是 MessageFactory 的集合，用于将多条消息组合为一条聚合消息。

目前 SAA 内置的聚合消息类型有且仅有 `AggregatedMessageFactory`。

所谓聚合消息，是指包含了多条 MessageFactory 的消息，最为经典的表现形式，是QQ的合并转发消息。

```python
from nonebot_plugin_saa import Text, Image, MessageFactory, AggregatedMessageFactory

mf1 = MessageFactory([Text("Hello World"), Image("http://example.com/image.png")])
mf2 = MessageFactory([Text("こんにちは　せかい"), Image("http://example.com/shashin.png")])

amf = AggregatedMessageFactory([mf1, mf2])
```

:::warning[支持情况]

需要注意的是，不是所有 SAA 适配了的 Adapter 都支持聚合消息。

如果将聚合消息发送给不支持的 Adapter，将会 fallback 到普通的 MessageFactory，也就是分条发送。

:::
