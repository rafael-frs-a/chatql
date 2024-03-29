from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from fastapi import FastAPI
from src import api, config, db
from src.api.graphql.broadcast import broadcast


async def start_app() -> None:
    await db.init_db(config.DB_NAME)
    await broadcast.connect()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    await start_app()
    yield


app = FastAPI(title=config.APP_NAME, lifespan=lifespan)
api.init_app(app)
