import typing as t
from functools import wraps
from strawberry.types import Info
from src.api.graphql import schemas
from src.api.graphql.auth import services


def login_required(f: t.Callable[..., t.Any]) -> t.Any:
    @wraps(f)
    def wrapper(*args: t.Any, **kwargs: t.Any) -> t.Any:
        info: Info[dict[t.Any, t.Any], t.Any] = kwargs["info"]
        auth_header = info.context["request"].headers.get("Authorization") or ""
        service = services.AuthService()
        validation_result = service.validate_authentication_header(auth_header)

        if validation_result.errors:
            errors = [
                schemas.ApiError(
                    code=schemas.ErrorEnum.UNAUTHORIZED,
                    title="Login required",
                    source=schemas.ApiErrorSource(header="Authorization"),
                ),
            ]
            return schemas.ApiResponse(errors=errors)

        info.context["userId"] = validation_result.data
        kwargs["info"] = info
        return f(*args, **kwargs)

    return wrapper
