import pytest
from datetime import timedelta
from src import utils
from src.api.enums import TokenType
from src.db.models import user as user_models
from src.db.models import message as message_models
from src.api import utils as api_utils


@pytest.fixture
async def jon() -> user_models.User:
    user = user_models.User(email="jon@doe.com")
    user = await user.save()
    return user


@pytest.fixture
async def mary() -> user_models.User:
    user = user_models.User(email="mary@doe.com")
    user = await user.save()
    return user


@pytest.fixture
async def common_channel(
    jon: user_models.User, mary: user_models.User
) -> message_models.Channel:
    channel = message_models.Channel(members=[jon, mary])
    channel = await channel.save()
    return channel


@pytest.fixture
async def jon_channel(jon: user_models.User) -> message_models.Channel:
    channel = message_models.Channel(members=[jon])
    channel = await channel.save()
    return channel


@pytest.fixture
async def mary_channel(mary: user_models.User) -> message_models.Channel:
    channel = message_models.Channel(members=[mary])
    channel = await channel.save()
    return channel


@pytest.fixture
def jon_token(jon: user_models.User) -> str:
    payload = {
        "userId": str(jon.id),
        "exp": utils.now() + timedelta(seconds=30),
        "type": TokenType.ACCESS_TOKEN,
    }
    return api_utils.make_app_token(payload)
