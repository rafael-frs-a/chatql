import typing as t
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
            getChannels {
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
    result_data = response_json["data"]["getChannels"]
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
            getChannels {
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
    result_data = response_json["data"]["getChannels"]
    assert not result_data["success"]
    assert result_data["errors"]
    assert len(result_data["errors"]) == 1
    error = result_data["errors"][0]
    assert error["code"] == schemas.ErrorEnum.USER_NOT_FOUND
    assert error["title"] == "Test error"


@pytest.mark.asyncio
async def test_success(
    jon: User,
    mary: User,
    jon_token: str,
    common_channel: message_models.Channel,
    jon_channel: message_models.Channel,
    mary_channel: message_models.Channel,  # Expected not to be returned by query
) -> None:
    query = """
        query TestQuery {
            getChannels {
                success
                data {
                    id
                    members {
                        id
                    }
                }
            }
        }
    """
    headers = {"Authorization": f"Bearer {jon_token}"}

    expected_data: list[dict[str, t.Any]] = [
        {
            "id": str(common_channel.id),
            "members": sorted(
                [{"id": str(jon.id)}, {"id": str(mary.id)}],
                key=lambda member: member["id"],
            ),
        },
        {
            "id": str(jon_channel.id),
            "members": [{"id": str(jon.id)}],
        },
    ]
    expected_data.sort(key=lambda channel: channel["id"])

    with TestClient(app) as client:
        response = client.post("/graphql", json={"query": query}, headers=headers)

    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    result_data = response_json["data"]["getChannels"]
    assert result_data["success"]
    assert result_data["data"] == expected_data
