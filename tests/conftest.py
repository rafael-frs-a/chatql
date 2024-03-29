import typing as t
import pytest
from src import db, config


@pytest.fixture(scope="function", autouse=True)
async def create_test_db() -> t.AsyncGenerator[None, None]:
    prefix = "test_"
    config.DB_NAME = prefix + config.DB_NAME
    client = await db.init_db(config.DB_NAME)
    yield
    await client.drop_database(config.DB_NAME)
    prefix_size = len(prefix)
    config.DB_NAME = config.DB_NAME[prefix_size:]
