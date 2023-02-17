from io import BytesIO
from pathlib import Path

from ..utils import MessageFactory, MessageSegmentFactory


class Text(MessageSegmentFactory):
    def __init__(self, text: str) -> None:
        self.data = {"text": text}


MessageFactory.register_text_ms(lambda text: Text(text))


class Image(MessageSegmentFactory):
    def __init__(self, image: str | bytes | Path | BytesIO) -> None:
        self.data = {"image": image}
