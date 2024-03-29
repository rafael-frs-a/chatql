import typing as t
import strawberry
from strawberry.types import Info
from src.api.graphql import schemas
from src.api.graphql.auth.decorators import login_required
from src.api.graphql.users import services
from src.api.graphql.users import schemas as user_schemas
from src.db.models import user as user_models


@strawberry.type
class Query:
    @strawberry.field
    @login_required
    async def get_users(
        self,
        info: Info[dict[t.Any, t.Any], t.Any],
    ) -> schemas.ApiResponse[list[user_schemas.User]]:
        service = services.UserService()
        return await service.get_users()

    @strawberry.field
    @login_required
    async def get_user(
        self, info: Info[dict[t.Any, t.Any], t.Any], user_id: str
    ) -> schemas.ApiResponse[user_schemas.User]:
        user_validator = user_schemas.UserValidator(
            userId=user_id, errorSource=schemas.ApiErrorSource(pointer="/userId")
        )
        errors = await user_validator.validate()

        if errors:
            return schemas.ApiResponse(errors=errors)

        user = t.cast(user_models.User, user_validator.user)
        data = user_schemas.User(user)
        return schemas.ApiResponse(data=data)
