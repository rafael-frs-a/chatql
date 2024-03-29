import typing as t
import beanie
from pydantic import EmailStr, Field
from src.db.models import base


if t.TYPE_CHECKING:
    from .message import Channel  # pragma: no cover


class User(base.TimestampMixin):
    email: t.Annotated[EmailStr, beanie.Indexed(unique=True)]
    channels: list[beanie.BackLink["Channel"]] = Field(original_field="members")  # type: ignore[call-arg]

    class Settings:
        name = "users"
