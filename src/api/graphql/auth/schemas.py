import typing as t
import strawberry
from src import config
from src.api import utils
from src.api.enums import TokenType
from src.api.graphql import schemas


@strawberry.type
class AuthenticationCredentials:
    accessToken: str
    refreshToken: str


@strawberry.input
class UserAuthenticationInput(schemas.ApiInput):
    email: str
    tokenUrl: str

    def validate_email(self) -> t.Optional[schemas.ApiError]:
        if not utils.is_valid_email(self.email):
            return schemas.ApiError(
                code=schemas.ErrorEnum.INVALID_EMAIL_ADDRESS,
                title="Invalid email address",
                source=schemas.ApiErrorSource(pointer="/email"),
            )

        return None

    def validate_url(self) -> t.Optional[schemas.ApiError]:
        if not utils.is_valid_url(self.tokenUrl):
            return schemas.ApiError(
                code=schemas.ErrorEnum.INVALID_URL,
                title="Invalid URL",
                source=schemas.ApiErrorSource(pointer="/tokenUrl"),
            )

        for cors_url in config.ALLOWED_ORIGINS:
            if self.tokenUrl.startswith(cors_url):
                break
        else:
            return schemas.ApiError(
                code=schemas.ErrorEnum.URL_NOT_SUPPORTED,
                title="URL not supported by API",
                source=schemas.ApiErrorSource(pointer="/tokenUrl"),
            )

        return None

    async def validate(self) -> list[schemas.ApiError]:
        email_error = self.validate_email()
        url_error = self.validate_url()
        errors = [email_error, url_error]
        filtered_errors = [_ for _ in errors if _]
        return filtered_errors


@strawberry.input
class RefreshTokenInput(schemas.ApiInput):
    refreshToken: str
    userId: strawberry.Private[t.Optional[str]] = None

    def validate_refresh_token(self) -> t.Optional[schemas.ApiError]:
        decode_result = utils.decode_app_token(self.refreshToken)

        if decode_result.errors:
            error = decode_result.errors[0]
            error.source = schemas.ApiErrorSource(pointer="/refreshToken")
            return error

        token = decode_result.data

        if not token or token["type"] != TokenType.REFRESH_TOKEN:
            return schemas.ApiError(
                code=schemas.ErrorEnum.INCORRECT_TOKEN_TYPE,
                title="Incorrect token type",
                source=schemas.ApiErrorSource(pointer="/refreshToken"),
            )

        self.userId = str(token.get("userId"))
        return None

    async def validate(self) -> list[schemas.ApiError]:
        refresh_token_error = self.validate_refresh_token()
        errors = [refresh_token_error]
        filtered_errors = [_ for _ in errors if _]
        return filtered_errors
