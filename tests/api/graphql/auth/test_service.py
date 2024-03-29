import pytest
from datetime import timedelta
from src import utils
from src.api import utils as api_utils
from src.api.enums import TokenType
from src.api.graphql import schemas
from src.api.graphql.auth import services


@pytest.mark.parametrize(
    "header_value,expected_error_title",
    [
        ("Basic invalid-token", "Invalid authentication header"),
        ("Bearer invalid-token", "Invalid token"),
    ],
)
def test_validate_authentication_header_invalid_token(
    header_value: str, expected_error_title: str
) -> None:
    service = services.AuthService()
    result = service.validate_authentication_header(header_value)

    assert result.errors
    assert len(result.errors) == 1
    error = result.errors[0]
    assert error.code == schemas.ErrorEnum.INVALID_TOKEN
    assert error.title == expected_error_title


def test_validate_authentication_header_incorrect_token() -> None:
    service = services.AuthService()
    payload = {
        "userId": "123",
        "exp": utils.now() + timedelta(seconds=10),
        "type": TokenType.REFRESH_TOKEN,
    }
    token = api_utils.make_app_token(payload)
    result = service.validate_authentication_header(f"Bearer {token}")

    assert result.errors
    assert len(result.errors) == 1
    error = result.errors[0]
    assert error.code == schemas.ErrorEnum.INCORRECT_TOKEN_TYPE


def test_validate_authentication_header_success() -> None:
    service = services.AuthService()
    payload = {
        "userId": "123",
        "exp": utils.now() + timedelta(seconds=10),
        "type": TokenType.ACCESS_TOKEN,
    }
    token = api_utils.make_app_token(payload)
    result = service.validate_authentication_header(f"Bearer {token}")

    assert not result.errors
    assert result.data == payload["userId"]
