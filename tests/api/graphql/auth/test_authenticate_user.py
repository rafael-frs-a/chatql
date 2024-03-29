import pytest
from src import config
from src.api.graphql import schema
from src.api.graphql import schemas
from src.db.models.user import User


@pytest.mark.asyncio
async def test_invalid_email_url() -> None:
    mutation = """
        mutation TestMutation($payload: UserAuthenticationInput!) {
            authenticateUser(payload: $payload) {
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
            "email": "invalid-email",
            "tokenUrl": "invalid-url",
        }
    }
    result = await schema.execute(mutation, variable_values=variables)
    assert result.errors is None
    assert result.data
    result_data = result.data["authenticateUser"]
    assert result_data["success"] is False
    expected_errors = [
        {
            "code": schemas.ErrorEnum.INVALID_EMAIL_ADDRESS,
            "source": {"pointer": "/email"},
        },
        {"code": schemas.ErrorEnum.INVALID_URL, "source": {"pointer": "/tokenUrl"}},
    ]

    for error in result_data["errors"]:
        assert error in expected_errors
        expected_errors.remove(error)

    assert not expected_errors


@pytest.mark.asyncio
async def test_not_supported_url() -> None:
    mutation = """
        mutation TestMutation($payload: UserAuthenticationInput!) {
            authenticateUser(payload: $payload) {
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
            "email": "test@mail.com",
            "tokenUrl": "https://fake.domain.com",
        }
    }
    result = await schema.execute(mutation, variable_values=variables)
    assert result.errors is None
    assert result.data
    result_data = result.data["authenticateUser"]
    assert result_data["success"] is False
    expected_errors = [
        {
            "code": schemas.ErrorEnum.URL_NOT_SUPPORTED,
            "source": {"pointer": "/tokenUrl"},
        },
    ]

    for error in result_data["errors"]:
        assert error in expected_errors
        expected_errors.remove(error)

    assert not expected_errors


@pytest.mark.asyncio
async def test_success() -> None:
    mutation = """
        mutation TestMutation($payload: UserAuthenticationInput!) {
            authenticateUser(payload: $payload) {
                success
                data
            }
        }
    """
    variables = {
        "payload": {
            "email": "test@mail.com",
            "tokenUrl": config.ALLOWED_ORIGINS[0],
        }
    }
    db_user = await User.find_one(User.email == variables["payload"]["email"])
    assert db_user is None

    result = await schema.execute(mutation, variable_values=variables)
    assert result.errors is None
    assert result.data
    result_data = result.data["authenticateUser"]
    assert result_data["success"] is True

    db_user = await User.find_one(User.email == variables["payload"]["email"])
    assert db_user is not None
    assert await User.find(User.email == variables["payload"]["email"]).count() == 1

    new_result = await schema.execute(mutation, variable_values=variables)
    assert new_result == result
    assert await User.find(User.email == variables["payload"]["email"]).count() == 1
