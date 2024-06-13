from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from redis import Redis as RedisSync
from redis.asyncio.client import Redis

from .config import Settings

redis_sync: RedisSync = RedisSync.from_url(Settings.redis_uri)
redis: Redis = Redis.from_url(Settings.redis_uri)


async def init_db():
    client = AsyncIOMotorClient(Settings.mongo_uri)
    db = client.get_database("fastapi_launchpad")
    await init_beanie(
        database=db,
        document_models=[],
    )
    return db
