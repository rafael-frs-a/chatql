import pytest
from fastapi import status
from fastapi.testclient import TestClient
from src.app import app
from src.api.graphql import schemas
from src.db.models import user as user_models
from src.db.models import message as message_models


@pytest.mark.asyncio
async def test_unauthenticated() -> None:
    query = """
        mutation TestMutation($payload: CreateMessageInput!) {
            createMessage(payload: $payload) {
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
        "payload": {
            "content": "",
        }
    }

    with TestClient(app) as client:
        response = client.post(
            "/graphql", json={"query": query, "variables": variables}
        )

    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    result_data = response_json["data"]["createMessage"]
    assert not result_data["success"]
    assert result_data["errors"]
    assert len(result_data["errors"]) == 1
    error = result_data["errors"][0]
    assert error["code"] == schemas.ErrorEnum.UNAUTHORIZED
    assert error["source"]["header"] == "Authorization"


@pytest.mark.asyncio
async def test_missing_input(jon_token: str) -> None:
    query = """
        mutation TestMutation($payload: CreateMessageInput!) {
            createMessage(payload: $payload) {
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
        "payload": {
            "content": "",
        }
    }
    headers = {"Authorization": f"Bearer {jon_token}"}

    with TestClient(app) as client:
        response = client.post(
            "/graphql", json={"query": query, "variables": variables}, headers=headers
        )

    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    result_data = response_json["data"]["createMessage"]
    assert not result_data["success"]
    expected_errors = [
        {
            "code": schemas.ErrorEnum.FIELD_REQUIRED,
            "source": {"pointer": "/content"},
        },
        {
            "code": schemas.ErrorEnum.FIELD_REQUIRED,
            "source": {"pointer": "/channelId"},
        },
    ]

    for error in result_data["errors"]:
        assert error in expected_errors
        expected_errors.remove(error)

    assert not expected_errors


@pytest.mark.asyncio
async def test_wrong_channel(
    mary_channel: message_models.Channel, jon_token: str
) -> None:
    query = """
        mutation TestMutation($payload: CreateMessageInput!) {
            createMessage(payload: $payload) {
                success
                errors {
                    code
                }
            }
        }
    """
    variables = {
        "payload": {
            "content": "Trying to hack Mary's inbox",
            "channelId": str(mary_channel.id),
        }
    }
    headers = {"Authorization": f"Bearer {jon_token}"}

    with TestClient(app) as client:
        response = client.post(
            "/graphql", json={"query": query, "variables": variables}, headers=headers
        )

    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    result_data = response_json["data"]["createMessage"]
    assert not result_data["success"]
    expected_errors = [
        {
            "code": schemas.ErrorEnum.MESSAGE_SENDER_NOT_IN_CHANNEL,
        }
    ]

    for error in result_data["errors"]:
        assert error in expected_errors
        expected_errors.remove(error)

    assert not expected_errors


@pytest.mark.asyncio
async def test_no_channel(
    jon: user_models.User, mary: user_models.User, jon_token: str
) -> None:
    query = """
        mutation TestMutation($payload: CreateMessageInput!) {
            createMessage(payload: $payload) {
                success
                data {
                    content
                    channel {
                        members {
                            id
                        }
                    }
                    sender {
                        id
                    }
                }
            }
        }
    """
    variables = {
        "payload": {
            "content": "Message to Mary",
            "channelMemberIds": [str(mary.id), str(mary.id)],
        }
    }
    headers = {"Authorization": f"Bearer {jon_token}"}

    with TestClient(app) as client:
        response = client.post(
            "/graphql", json={"query": query, "variables": variables}, headers=headers
        )

    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    result_data = response_json["data"]["createMessage"]
    assert result_data["success"]
    message = result_data["data"]
    channel_members = message["channel"]["members"]
    channel_member_ids = sorted([member["id"] for member in channel_members])
    expected_member_ids = sorted([str(jon.id), str(mary.id)])
    assert channel_member_ids == expected_member_ids
    assert message["sender"]["id"] == str(jon.id)
    assert message["content"] == variables["payload"]["content"]


@pytest.mark.asyncio
async def test_with_channel(
    jon: user_models.User, common_channel: message_models.Channel, jon_token: str
) -> None:
    query = """
        mutation TestMutation($payload: CreateMessageInput!) {
            createMessage(payload: $payload) {
                success
                data {
                    content
                    channel {
                        id
                    }
                    sender {
                        id
                    }
                }
                errors {
                    code
                    title
                }
            }
        }
    """
    variables = {
        "payload": {
            "content": "Message to Mary",
            "channelId": str(common_channel.id),
        }
    }
    headers = {"Authorization": f"Bearer {jon_token}"}

    with TestClient(app) as client:
        response = client.post(
            "/graphql", json={"query": query, "variables": variables}, headers=headers
        )

    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    result_data = response_json["data"]["createMessage"]
    assert result_data["success"]
    message = result_data["data"]
    assert message["channel"]["id"] == str(common_channel.id)
    assert message["sender"]["id"] == str(jon.id)
    assert message["content"] == variables["payload"]["content"]
