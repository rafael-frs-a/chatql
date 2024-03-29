import strawberry
from src.api.graphql import schemas
from src.api.graphql.auth import schemas as auth_schemas
from src.api.graphql.auth import services


@strawberry.type
class Mutation:
    @strawberry.mutation
    async def authenticate_user(
        self, payload: auth_schemas.UserAuthenticationInput
    ) -> schemas.ApiResponse[str]:
        errors = await payload.validate()

        if errors:
            return schemas.ApiResponse(errors=errors)

        service = services.AuthService()
        return await service.authenticate_user(payload)

    @strawberry.mutation
    async def refresh_token(
        self, payload: auth_schemas.RefreshTokenInput
    ) -> schemas.ApiResponse[auth_schemas.AuthenticationCredentials]:
        errors = await payload.validate()

        if errors:
            return schemas.ApiResponse(errors=errors)

        service = services.AuthService()
        return service.refresh_token(payload)
