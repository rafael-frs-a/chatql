import pytest
from fastapi import status
from fastapi.testclient import TestClient
from src.app import app
from src.api.graphql import schemas
from src.db.models.user import User


@pytest.mark.asyncio
async def test_unauthenticated() -> None:
    query = """
        query TestQuery {
            getUsers {
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
    result_data = response_json["data"]["getUsers"]
    assert not result_data["success"]
    assert result_data["errors"]
    assert len(result_data["errors"]) == 1
    error = result_data["errors"][0]
    assert error["code"] == schemas.ErrorEnum.UNAUTHORIZED
    assert error["source"]["header"] == "Authorization"


@pytest.mark.asyncio
async def test_success(jon: User, mary: User, jon_token: str) -> None:
    users = [
        {"email": jon.email, "id": str(jon.id)},
        {"email": mary.email, "id": str(mary.id)},
    ]
    users.sort(key=lambda user: user["email"])
    expected_data = [user for user in users]

    query = """
        query TestQuery {
            getUsers {
                success
                data {
                    id
                    email
                }
            }
        }
    """
    headers = {"Authorization": f"Bearer {jon_token}"}

    with TestClient(app) as client:
        response = client.post("/graphql", json={"query": query}, headers=headers)

    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    result_data = response_json["data"]["getUsers"]
    assert result_data["success"]
    assert result_data["data"] == expected_data
