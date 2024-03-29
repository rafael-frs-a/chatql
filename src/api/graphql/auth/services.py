from datetime import timedelta
from src import config, utils
from src.api import utils as api_utils
from src.api.enums import TokenType
from src.api.graphql import schemas
from src.api.graphql.auth import clients
from src.api.graphql.auth import schemas as auth_schemas
from src.api.graphql.users import stores as user_stores


class AuthService:
    def __init__(self) -> None:
        self.email_client = clients.EmailClient()
        self.user_store = user_stores.UserStore()

    def generate_credentials(
        self, user_id: str
    ) -> auth_schemas.AuthenticationCredentials:
        payload = {
            "userId": user_id,
            "exp": utils.now() + timedelta(seconds=config.ACCESS_TOKEN_EXP_SECONDS),
            "type": TokenType.ACCESS_TOKEN,
        }
        access_token = api_utils.make_app_token(payload)
        payload = {
            "userId": user_id,
            "exp": utils.now() + timedelta(seconds=config.REFRESH_TOKEN_EXP_SECONDS),
            "type": TokenType.REFRESH_TOKEN,
        }
        refresh_token = api_utils.make_app_token(payload)
        return auth_schemas.AuthenticationCredentials(
            accessToken=access_token, refreshToken=refresh_token
        )

    async def authenticate_user(
        self, payload: auth_schemas.UserAuthenticationInput
    ) -> schemas.ApiResponse[str]:
        user = await self.user_store.get_or_create_user(payload.email)
        credentials = self.generate_credentials(str(user.id))
        return await self.email_client.send_authentication_email(
            credentials, payload.tokenUrl
        )

    def refresh_token(
        self, payload: auth_schemas.RefreshTokenInput
    ) -> schemas.ApiResponse[auth_schemas.AuthenticationCredentials]:
        credentials = self.generate_credentials(str(payload.userId))
        return schemas.ApiResponse(data=credentials)

    def validate_authentication_header(
        self, header_value: str
    ) -> schemas.ApiResponse[str]:
        if not header_value.startswith("Bearer "):
            error = schemas.ApiError(
                code=schemas.ErrorEnum.INVALID_TOKEN,
                title="Invalid authentication header",
            )
            return schemas.ApiResponse(errors=[error])

        token = header_value.lstrip("Bearer").strip()
        decode_result = api_utils.decode_app_token(token)

        if decode_result.errors:
            return schemas.ApiResponse(errors=decode_result.errors)

        decoded_token = decode_result.data

        if not decoded_token or decoded_token["type"] != TokenType.ACCESS_TOKEN:
            error = schemas.ApiError(
                code=schemas.ErrorEnum.INCORRECT_TOKEN_TYPE,
                title="Incorrect token type",
            )
            return schemas.ApiResponse(errors=[error])

        user_id = decoded_token.get("userId", "")
        return schemas.ApiResponse(data=user_id)
