import pytest
from src.api.graphql import schemas
from src.api.graphql.users import schemas as user_schemas


@pytest.mark.asyncio
@pytest.mark.parametrize("user_id", ["", "123456789012345678901234"])
async def test_user_validator_user_not_found(user_id: str) -> None:
    schema = user_schemas.UserValidator(userId=user_id)
    error = await schema.validate_user_id()
    assert error
    assert error.code == schemas.ErrorEnum.USER_NOT_FOUND
