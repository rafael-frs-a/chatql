import typing as t
import jwt
import validators
from src import config
from src.api.graphql import schemas


def make_app_token(payload: dict[str, t.Any]) -> str:
    return jwt.encode(
        payload,
        config.SECRET_KEY,
        algorithm=config.JWT_ALGORITHM,
    )


def decode_jwt_token(
    token: str,
    key: str = "",
    algorithms: t.Optional[list[str]] = None,
    verify_signature: bool = True,
) -> schemas.ApiResponse[dict[str, t.Any]]:
    try:
        options = {"verify_signature": verify_signature}
        content = jwt.decode(token, key, algorithms=algorithms, options=options)
        return schemas.ApiResponse(data=content)
    except jwt.exceptions.ExpiredSignatureError:
        error = schemas.ApiError(
            code=schemas.ErrorEnum.EXPIRED_TOKEN, title="Expired token"
        )
        return schemas.ApiResponse(errors=[error])
    except jwt.exceptions.InvalidTokenError:
        error = schemas.ApiError(
            code=schemas.ErrorEnum.INVALID_TOKEN, title="Invalid token"
        )
        return schemas.ApiResponse(errors=[error])


def decode_app_token(token: str) -> schemas.ApiResponse[dict[str, t.Any]]:
    return decode_jwt_token(
        token,
        config.SECRET_KEY,
        [config.JWT_ALGORITHM],
    )


def is_valid_email(email: str) -> bool:
    return validators.email(email) is True


def is_valid_url(url: str) -> bool:
    for cors_url in config.ALLOWED_ORIGINS:
        if url.startswith(cors_url):
            return True

    return validators.url(url) is True
