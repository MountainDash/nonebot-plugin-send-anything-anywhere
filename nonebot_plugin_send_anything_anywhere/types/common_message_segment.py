from ..utils import MessageSegmentFactory


class Text(MessageSegmentFactory):
    text: str

    def __init__(self, text: str) -> None:
        self.text = text
