import typing as t
import strawberry
from datetime import datetime
from beanie import PydanticObjectId
from bson.errors import InvalidId
from src.api.graphql import schemas
from src.db.models import user as user_models


@strawberry.type
class User:
    id: str
    email: str
    createdAt: datetime
    updatedAt: datetime

    def __init__(self, user: user_models.User) -> None:
        self.id = str(user.id)
        self.email = user.email
        self.createdAt = user.created_at
        self.updatedAt = user.updated_at


@strawberry.input
class UserValidator(schemas.ApiInput):
    userId: str
    user: strawberry.Private[t.Optional[User]] = None
    errorSource: strawberry.Private[t.Optional[schemas.ApiErrorSource]] = None

    async def validate_user_id(self) -> t.Optional[schemas.ApiError]:
        try:
            self.user = await user_models.User.find_one(
                user_models.User.id == PydanticObjectId(self.userId), fetch_links=True
            )
        except InvalidId:
            pass

        if not self.user:
            return schemas.ApiError(
                code=schemas.ErrorEnum.USER_NOT_FOUND,
                title="User not found",
                source=self.errorSource,
            )

        return None

    async def validate(self) -> list[schemas.ApiError]:
        user_id_error = await self.validate_user_id()
        errors = [user_id_error]
        filtered_errors = [_ for _ in errors if _]
        return filtered_errors
