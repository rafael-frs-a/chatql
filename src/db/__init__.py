from beanie import init_beanie
from motor.motor_asyncio import AsyncIOMotorClient
from motor.core import AgnosticClient
from src import config
from src.db.models import base
from src.db.models import user
from src.db.models import message


async def init_db(db_name: str) -> AgnosticClient:  # type: ignore[type-arg]
    client: AgnosticClient = AsyncIOMotorClient(config.DB_CONNECTION_STRING)  # type: ignore[type-arg]
    await init_beanie(
        database=client[db_name],
        document_models=[
            base.Counter,
            user.User,
            message.Channel,
            message.Message,
        ],
    )
    return client
