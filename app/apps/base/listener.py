import json
from typing import Type, TypeVar

from server import db

from .models import TaskBaseEntity

T = TypeVar("T", bound=TaskBaseEntity)


async def channel_listener(entity_class: Type[T]):
    channel_name = f"{entity_class.__name__.lower()}_channel"

    pubsub = db.dragonfly.pubsub()
    await pubsub.subscribe(channel_name)
    async for message in pubsub.listen():
        if message["type"] == "message":
            entity = entity_class(**json.loads(message["data"].decode("utf-8")))
            await entity.save_and_emit()
