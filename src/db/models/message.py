import typing as t
import beanie
import pymongo
from pydantic import Field
from src.db.models import base
from src.db.models import user


class Channel(base.TimestampMixin):
    members: list[beanie.Link[user.User]]
    messages: list[beanie.BackLink["Message"]] = Field(original_field="channel")  # type: ignore[call-arg]

    class Settings:
        name = "channels"


class Message(base.TimestampMixin):
    sender: beanie.Link[user.User]
    channel: beanie.Link[Channel]
    content: t.Annotated[str, beanie.Indexed(index_type=pymongo.TEXT)]
    sequence: t.Annotated[int, beanie.Indexed(unique=True)]  # used for pagination

    class Settings:
        name = "messages"
