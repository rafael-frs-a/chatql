import typing as t
import beanie
from enum import Enum
from datetime import datetime
from pydantic import Field
from src import utils


class TimestampMixin(beanie.Document):
    created_at: datetime = Field(default_factory=utils.now)
    updated_at: datetime = Field(default_factory=utils.now)

    @beanie.before_event(beanie.Replace, beanie.Save)  # type: ignore[misc]
    def update_updated_at(self) -> None:
        self.updated_at = utils.now()


class CounterType(str, Enum):
    MESSAGE = "MESSAGE"


class Counter(beanie.Document):
    type: t.Annotated[CounterType, beanie.Indexed(unique=True)]
    next_value: int = 1

    class Settings:
        name = "counters"
