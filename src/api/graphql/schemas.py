import uuid
import typing as t
import strawberry
from abc import ABC, abstractmethod
from enum import Enum

TData = t.TypeVar("TData")


@strawberry.enum
class ErrorEnum(str, Enum):
    CHANNEL_NOT_FOUND = "CHANNEL_NOT_FOUND"
    EXPIRED_TOKEN = "EXPIRED_TOKEN"  # nosec
    FIELD_REQUIRED = "FIELD_REQUIRED"
    INCORRECT_TOKEN_TYPE = "INCORRECT_TOKEN_TYPE"  # nosec
    INVALID_EMAIL_ADDRESS = "INVALID_EMAIL_ADDRESS"
    INVALID_TOKEN = "INVALID_TOKEN"  # nosec
    INVALID_URL = "INVALID_URL"
    MESSAGE_SENDER_NOT_IN_CHANNEL = "MESSAGE_SENDER_NOT_IN_CHANNEL"
    UNAUTHORIZED = "UNAUTHORIZED"
    URL_NOT_SUPPORTED = "URL_NOT_SUPPORTED"
    USER_NOT_FOUND = "USER_NOT_FOUND"


# Error object structure based on JSON:API specification: https://jsonapi.org/format/#error-objects
@strawberry.type
class ApiErrorSource:
    pointer: t.Optional[str] = None
    header: t.Optional[str] = None
    parameter: t.Optional[str] = None


@strawberry.type
class ApiError:
    id: uuid.UUID  # Useful for tracing errors on logs
    code: ErrorEnum
    title: str
    detail: t.Optional[str] = None
    source: t.Optional[ApiErrorSource] = None

    def __init__(
        self,
        code: ErrorEnum,
        title: str,
        detail: t.Optional[str] = None,
        source: t.Optional[ApiErrorSource] = None,
    ) -> None:
        self.id = uuid.uuid4()
        self.code = code
        self.title = title
        self.detail = detail
        self.source = source


@strawberry.type
class ApiResponse(t.Generic[TData]):
    data: t.Optional[TData] = None
    errors: t.Optional[list["ApiError"]] = None

    @strawberry.field
    def success(self) -> bool:
        return not self.errors


class ApiInput(ABC):
    @abstractmethod
    async def validate(self) -> list[ApiError]:
        raise NotImplementedError  # pragma: no cover
