import pytest
from fastapi import status
from fastapi.testclient import TestClient
from src.app import app
from src.api.graphql import schemas
from src.db.models.user import User


@pytest.mark.asyncio
async def test_unauthenticated() -> None:
    query = """
        query TestQuery($userId: String!) {
            getUser(userId: $userId) {
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
    variables = {
        "userId": "",
    }

    with TestClient(app) as client:
        response = client.post(
            "/graphql", json={"query": query, "variables": variables}
        )

    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    result_data = response_json["data"]["getUser"]
    assert not result_data["success"]
    assert result_data["errors"]
    assert len(result_data["errors"]) == 1
    error = result_data["errors"][0]
    assert error["code"] == schemas.ErrorEnum.UNAUTHORIZED
    assert error["source"]["header"] == "Authorization"


@pytest.mark.asyncio
@pytest.mark.parametrize("user_id", ["", "123456789012345678901234"])
async def test_invalid_user_id(user_id: str, jon_token: str) -> None:
    query = """
        query TestQuery($userId: String!) {
            getUser(userId: $userId) {
                success
                errors {
                    code
                    source {
                        pointer
                    }
                }
            }
        }
    """
    variables = {
        "userId": user_id,
    }
    headers = {"Authorization": f"Bearer {jon_token}"}

    with TestClient(app) as client:
        response = client.post(
            "/graphql", json={"query": query, "variables": variables}, headers=headers
        )

    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    result_data = response_json["data"]["getUser"]
    assert not result_data["success"]
    assert result_data["errors"]
    assert len(result_data["errors"]) == 1
    error = result_data["errors"][0]
    assert error["code"] == schemas.ErrorEnum.USER_NOT_FOUND
    assert error["source"]["pointer"] == "/userId"


@pytest.mark.asyncio
async def test_success(mary: User, jon_token: str) -> None:
    query = """
        query TestQuery($userId: String!) {
            getUser(userId: $userId) {
                success
                data {
                    id
                    email
                }
            }
        }
    """
    variables = {
        "userId": str(mary.id),
    }
    headers = {"Authorization": f"Bearer {jon_token}"}
    expected_data = {"email": mary.email, "id": str(mary.id)}

    with TestClient(app) as client:
        response = client.post(
            "/graphql", json={"query": query, "variables": variables}, headers=headers
        )

    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    result_data = response_json["data"]["getUser"]
    assert result_data["success"]
    assert result_data["data"] == expected_data
