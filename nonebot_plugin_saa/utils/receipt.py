from abc import ABC
from typing import Any

from pydantic import BaseModel


class Receipt(BaseModel, ABC, arbitrary_types_allowed=True):
    async def revoke(self):
        ...

    @property
    def raw(self) -> Any:
        ...


class TODOReceipt(Receipt):
    data: Any

    @property
    def raw(self):
        return self.data
