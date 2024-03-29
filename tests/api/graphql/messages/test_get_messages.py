import pytest
from fastapi import status
from fastapi.testclient import TestClient
from src.app import app
from src.api.graphql import schemas
from src.api.graphql.users.schemas import UserValidator
from src.db.models.user import User
from src.db.models import message as message_models
from tests.api.graphql import utils as test_utils


@pytest.mark.asyncio
async def test_unauthenticated() -> None:
    query = """
        query TestQuery {
            getMessages {
                success
                errors {
                    code
                    source {
                        header
                    }
                }
            }
        }
    """

    with TestClient(app) as client:
        response = client.post("/graphql", json={"query": query})

    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    result_data = response_json["data"]["getMessages"]
    assert not result_data["success"]
    assert result_data["errors"]
    assert len(result_data["errors"]) == 1
    error = result_data["errors"][0]
    assert error["code"] == schemas.ErrorEnum.UNAUTHORIZED
    assert error["source"]["header"] == "Authorization"


@pytest.mark.asyncio
async def test_invalid_token(jon_token: str, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        UserValidator,
        "validate",
        test_utils.patch_authenticated_user_validator,
    )
    query = """
        query TestQuery {
            getMessages {
                success
                errors {
                    code
                    title
                }
            }
        }
    """
    headers = {"Authorization": f"Bearer {jon_token}"}

    with TestClient(app) as client:
        response = client.post("/graphql", json={"query": query}, headers=headers)

    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    result_data = response_json["data"]["getMessages"]
    assert not result_data["success"]
    assert result_data["errors"]
    assert len(result_data["errors"]) == 1
    error = result_data["errors"][0]
    assert error["code"] == schemas.ErrorEnum.USER_NOT_FOUND
    assert error["title"] == "Test error"


@pytest.mark.asyncio
async def test_success(jon: User, mary: User, jon_token: str) -> None:
    query = """
        query TestQuery($content: String) {
            getMessages(content: $content) {
                success
                data {
                    id
                    channel {
                        id
                    }
                    sender {
                        id
                    }
                    content
                    sequence
                }
            }
        }
    """
    variables = {
        "content": "message myself",
    }
    headers = {"Authorization": f"Bearer {jon_token}"}

    jon_channel = await message_models.Channel(members=[jon]).save()
    mary_channel = await message_models.Channel(members=[mary]).save()
    message = await message_models.Message(
        channel=jon_channel, sender=jon, content="Message to myself", sequence=1
    ).save()
    await message_models.Message(
        channel=mary_channel, sender=mary, content="Message to myself", sequence=2
    ).save()

    with TestClient(app) as client:
        response = client.post(
            "/graphql", json={"query": query, "variables": variables}, headers=headers
        )

    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    result_data = response_json["data"]["getMessages"]
    assert result_data["success"]
    assert len(result_data["data"]) == 1
    data_message = result_data["data"][0]
    assert data_message["id"] == str(message.id)
    assert data_message["sequence"] == message.sequence
    assert data_message["content"] == message.content
    assert data_message["channel"]["id"] == str(jon_channel.id)
    assert data_message["sender"]["id"] == str(jon.id)
