import pytest
from datetime import timedelta
from src import utils
from src.api import utils as api_utils
from src.api.enums import TokenType
from src.api.graphql import schema
from src.api.graphql import schemas


@pytest.mark.asyncio
async def test_invalid_token() -> None:
    mutation = """
        mutation TestMutation($payload: RefreshTokenInput!) {
            refreshToken(payload: $payload) {
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
            "refreshToken": "invalid-token",
        }
    }
    result = await schema.execute(mutation, variable_values=variables)
    assert result.errors is None
    assert result.data
    result_data = result.data["refreshToken"]
    assert result_data["success"] is False
    assert len(result_data["errors"]) == 1
    error = result_data["errors"][0]
    assert error["code"] == schemas.ErrorEnum.INVALID_TOKEN
    assert error["source"]["pointer"] == "/refreshToken"


@pytest.mark.asyncio
async def test_expired_token() -> None:
    mutation = """
        mutation TestMutation($payload: RefreshTokenInput!) {
            refreshToken(payload: $payload) {
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
    payload = {
        "userId": "userId",
        "exp": utils.now() - timedelta(seconds=1),
        "type": TokenType.REFRESH_TOKEN,
    }
    refresh_token = api_utils.make_app_token(payload)
    variables = {
        "payload": {
            "refreshToken": refresh_token,
        }
    }
    result = await schema.execute(mutation, variable_values=variables)
    assert result.errors is None
    assert result.data
    result_data = result.data["refreshToken"]
    assert result_data["success"] is False
    assert len(result_data["errors"]) == 1
    error = result_data["errors"][0]
    assert error["code"] == schemas.ErrorEnum.EXPIRED_TOKEN
    assert error["source"]["pointer"] == "/refreshToken"


@pytest.mark.asyncio
async def test_incorrect_token() -> None:
    mutation = """
        mutation TestMutation($payload: RefreshTokenInput!) {
            refreshToken(payload: $payload) {
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
    payload = {
        "userId": "userId",
        "exp": utils.now() + timedelta(seconds=10),
        "type": TokenType.ACCESS_TOKEN,
    }
    refresh_token = api_utils.make_app_token(payload)
    variables = {
        "payload": {
            "refreshToken": refresh_token,
        }
    }
    result = await schema.execute(mutation, variable_values=variables)
    assert result.errors is None
    assert result.data
    result_data = result.data["refreshToken"]
    assert result_data["success"] is False
    assert len(result_data["errors"]) == 1
    error = result_data["errors"][0]
    assert error["code"] == schemas.ErrorEnum.INCORRECT_TOKEN_TYPE
    assert error["source"]["pointer"] == "/refreshToken"


@pytest.mark.asyncio
async def test_success() -> None:
    mutation = """
        mutation TestMutation($payload: RefreshTokenInput!) {
            refreshToken(payload: $payload) {
                success
                data {
                    accessToken
                    refreshToken
                }
            }
        }
    """
    payload = {
        "userId": "userId",
        "exp": utils.now() + timedelta(seconds=10),
        "type": TokenType.REFRESH_TOKEN,
    }
    refresh_token = api_utils.make_app_token(payload)
    variables = {
        "payload": {
            "refreshToken": refresh_token,
        }
    }
    result = await schema.execute(mutation, variable_values=variables)
    assert result.errors is None
    assert result.data
    result_data = result.data["refreshToken"]
    assert result_data["success"] is True
    assert result_data["data"]["accessToken"]
    assert result_data["data"]["refreshToken"]
