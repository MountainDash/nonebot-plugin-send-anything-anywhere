# 消息构建

## 内置的消息段类型 MessageSegmentFactory

SAA 内置的消息段类型有：

- `Text`：文本消息段
- `Image`：图片消息段
- `Reply`：回复消息段
- `Mention`：提及消息段

上述消息段类型都是 `MessageSegmentFactory` 的子类。

### Text

`Text` 用于包装文本消息，可以使用 `Text` 来包装任意文本消息(str)。

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

:::
