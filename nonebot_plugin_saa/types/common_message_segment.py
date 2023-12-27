from io import BytesIO
from pathlib import Path
from typing import Union, Literal, TypedDict

from ..registries import MessageId
from ..abstract_factories import MessageFactory, MessageSegmentFactory


class TextData(TypedDict):
    text: str


class Text(MessageSegmentFactory):
    """文本消息段"""

    type: Literal["text"] = "text"
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

    type: Literal["image"] = "image"
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


class MentionData(TypedDict):
    user_id: str


class Mention(MessageSegmentFactory):
    """提到其他用户"""

    type: Literal["mention"] = "mention"
    data: MentionData

    def __init__(self, user_id: str):
        """提到其他用户的消息段

        参数:
            user_id: 用户 ID
        """

        super().__init__()
        self.data = {"user_id": user_id}


class Reply(MessageSegmentFactory):
    """回复其他消息的消息段"""

    type: Literal["reply"] = "reply"
    data: MessageId

    def __init__(self, message_id: MessageId):
        """回复其他消息的消息段

        参数:
            message_id: 需要回复消息的 MessageId
        """

        super().__init__()
        self.data = message_id
