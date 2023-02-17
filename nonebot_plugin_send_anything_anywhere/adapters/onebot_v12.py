from io import BytesIO
from pathlib import Path
from functools import partial

from nonebot.adapters import Bot as BaseBot

from ..types import Text, Image
from ..utils import SupportedAdapters, register_ms_adapter

try:
    from nonebot.adapters.onebot.v12 import Bot, MessageSegment

    adapter = SupportedAdapters.onebot_v12
    register_nonebot_v12 = partial(register_ms_adapter, adapter)

    @register_nonebot_v12(Text)
    def _text(t: Text) -> MessageSegment:
        return MessageSegment.text(t.data["text"])

    @register_nonebot_v12(Image)
    async def _image(i: Image, bot: BaseBot) -> MessageSegment:
        if not isinstance(bot, Bot):
            raise TypeError(f"Unsupported type of bot: {type(bot)}")
        image: str | bytes | Path | BytesIO = i.data["image"]
        if isinstance(image, str):
            resp = await bot.upload_file(type="url", name="image", url=image)
        elif isinstance(image, Path):
            resp = await bot.upload_file(
                type="path", name="image", path=str(image.resolve())
            )
        elif isinstance(image, BytesIO):
            image = image.getvalue()
            resp = await bot.upload_file(type="data", name="image", data=image)
        elif isinstance(image, bytes):
            resp = await bot.upload_file(type="data", name="image", data=image)
        else:
            raise TypeError(f"Unsupported type of image: {type(image)}")

        file_id = resp["file_id"]
        return MessageSegment.image(file_id)

except ImportError:
    pass
except Exception as e:
    raise e
