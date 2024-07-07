from typing import TypeVar

from core.exceptions import BaseHTTPException
from fastapi import Request

from .models import BaseEntity, OwnedEntity

T = TypeVar("T", bound=BaseEntity)
OT = TypeVar("OT", bound=OwnedEntity)


def create_dto(cls: OT):
    async def dto(request: Request, user=None, **kwargs):
        form_data = await request.json()
        if user:
            form_data["user_id"] = user.uid
        return cls(**form_data)

    return dto


def update_dto(cls: OT):
    async def dto(request: Request, user=None, **kwargs):
        uid = request.path_params["uid"]
        form_data = await request.json()
        kwargs = {}
        if user:
            kwargs["user"] = user
        item = await cls.get_item(uid, **kwargs)

        if not item:
            raise BaseHTTPException(
                status_code=404,
                error="item_not_found",
                message="Item not found",
            )

        item_data = item.model_dump() | form_data

        return cls(**item_data)

    return dto
