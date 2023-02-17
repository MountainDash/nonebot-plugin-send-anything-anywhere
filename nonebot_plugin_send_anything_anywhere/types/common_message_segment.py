from io import BytesIO
from pathlib import Path
from typing import TypedDict

from ..utils import MessageFactory, MessageSegmentFactory


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
        self.data = {"text": text}


MessageFactory.register_text_ms(lambda text: Text(text))


class ImageData(TypedDict):
    image: str | bytes | Path | BytesIO
    name: str


class Image(MessageSegmentFactory):
    """图片消息段"""

    data: ImageData

    def __init__(
        self, image: str | bytes | Path | BytesIO, name: str = "image"
    ) -> None:
        """图片消息段

        支持多种格式的数据

        参数:
            image: str 为图片 URL，bytes 为图片数据，Path 为图片路径，BytesIO 为图片文件流
            name: 图片名称，默认为 image
        """
        self.data = {"image": image, "name": name}
