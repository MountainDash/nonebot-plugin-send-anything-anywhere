from ..utils import MessageFactory, MessageSegmentFactory


class Text(MessageSegmentFactory):
    def __init__(self, text: str) -> None:
        self.data = {"text": text}


MessageFactory.register_text_ms(lambda text: Text(text))
