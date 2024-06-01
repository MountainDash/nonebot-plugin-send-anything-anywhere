from io import BytesIO
from pathlib import Path
from typing_extensions import NotRequired
from typing import Dict, Union, TypedDict, overload

from ..registries import MessageId
from ..utils import SupportedAdapters
from ..abstract_factories import MessageFactory, MessageSegmentFactory


class TextData(TypedDict):
    text: str


class Text(MessageSegmentFactory):
    """文本消息段"""

    data: TextData

    def __init__(self, text: str) -> None:
        """文本消息段

        参数:
            text: 文本内容
        """
        super().__init__()
        self.data = {"text": text}

    def __str__(self) -> str:
        return self.data["text"]

    def __len__(self) -> int:
        return len(self.data["text"])


MessageFactory.register_text_ms(lambda text: Text(text))


class ImageData(TypedDict):
    image: Union[str, bytes, Path, BytesIO]
    name: str


class Image(MessageSegmentFactory):
    """图片消息段"""

    data: ImageData

    def __init__(
        self,
        image: Union[str, bytes, Path, BytesIO],
        name: str = "image",
    ) -> None:
        """图片消息段

        支持多种格式的数据

        参数:
            image: str 为图片 URL，bytes 为图片数据，Path 为图片路径，BytesIO 为图片文件流
            name: 图片名称，默认为 image
        """
        super().__init__()
        self.data = {"image": image, "name": name}

    def __str__(self) -> str:
        image = self.data["image"]
        format_template = "{0}={1}"
        if isinstance(image, bytes):
            image_str = format_template.format("image", f"<bytes {len(image)}>")
        elif isinstance(image, BytesIO):
            image_str = format_template.format(
                "image", f"<BytesIO {len(image.getvalue())}>"
            )
        else:
            image_str = format_template.format("image", repr(image))

        kv_list = list(f"{k}={v!r}" for k, v in self.data.items() if k != "image")
        kv_list.append(image_str)
        return f"[SAA:{self.__class__.__name__}|{','.join(kv_list)}]"

    def __repr__(self) -> str:
        image = self.data["image"]
        format_template = "{0}={1}"
        if isinstance(image, bytes):
            image_str = format_template.format("image", repr(image))
        elif isinstance(image, BytesIO):
            image_str = format_template.format(
                "image", f"BytesIO({repr(image.getvalue())})"
            )
        else:
            image_str = format_template.format("image", repr(image))
        kv_list = list(f"{k}={v!r}" for k, v in self.data.items() if k != "image")
        kv_list.append(image_str)
        return f"{self.__class__.__name__}({', '.join(kv_list)})"


class MentionData(TypedDict):
    user_id: str


class Mention(MessageSegmentFactory):
    """提到其他用户"""

    data: MentionData

    def __init__(self, user_id: str):
        """提到其他用户的消息段

        参数:
            user_id: 用户 ID
        """

        super().__init__()
        self.data = {"user_id": user_id}


class MentionAllData(TypedDict):
    online_only: bool
    fallback: Union[str, None]
    special_fallback: NotRequired[Dict[SupportedAdapters, str]]


class MentionAll(MessageSegmentFactory):
    """提到所有人"""

    data: MentionAllData

    @overload
    def __init__(self):
        ...

    # * 之后的参数只能通过关键字传递，方便 IDE 提示
    @overload
    def __init__(self, *, online_only: bool = False) -> None:
        ...

    # fallback 参数可以通过位置传递
    @overload
    def __init__(self, fallback: Union[str, None] = None) -> None:
        ...

    @overload
    def __init__(
        self,
        fallback: Union[str, None] = None,
        online_only: bool = False,
    ) -> None:
        ...

    def __init__(
        self,
        fallback: Union[str, None] = None,
        online_only: bool = False,
    ) -> None:
        """提到所有人的消息段

        参数:
            fallback: 当不支持提到所有人时的默认回退消息。
            手动指定的回退消息不会附带 `@` 字符，
            为 None 时使用平台中具体实现的回退消息段。

            online_only: 是否只提到当前在线用户，默认为 False。
            不支持的平台或者指定了回退消息时，会忽略此参数。
        """

        super().__init__()
        self.data = {"online_only": online_only, "fallback": fallback}

    def set_special_fallback(self, adapter: SupportedAdapters, fallback: str):
        """设置指定适配器的回退消息段，仅在不支持提到所有人时生效。

        在此设置的回退消息优先级高于默认回退消息。

        参数:
            adapter: 适配器
            fallback: 回退消息
        """
        if "special_fallback" not in self.data:
            self.data["special_fallback"] = {}
        self.data["special_fallback"][adapter] = fallback


class ReplyData(TypedDict):
    message_id: MessageId


class Reply(MessageSegmentFactory):
    """回复其他消息的消息段"""

    data: ReplyData

    def __init__(self, message_id: MessageId):
        """回复其他消息的消息段

        参数:
            message_id: 需要回复消息的 MessageId
        """
        super().__init__()
        self.data = {"message_id": message_id}
