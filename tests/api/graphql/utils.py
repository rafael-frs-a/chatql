import typing as t
from src.api.graphql import schemas


async def patch_authenticated_user_validator(
    *args: list[t.Any], **kwargs: dict[t.Any, t.Any]
) -> list[schemas.ApiError]:
    return [schemas.ApiError(code=schemas.ErrorEnum.USER_NOT_FOUND, title="Test error")]
