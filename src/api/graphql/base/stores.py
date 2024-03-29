import typing as t
from src.db.models import base as base_models


class BaseStore:
    async def get_counter_sequence(self, type_: base_models.CounterType) -> int:
        counter = await base_models.Counter.find_one(base_models.Counter.type == type_)

        if not counter:
            counter = base_models.Counter(type=type_)
            counter = await counter.save()

        counter = t.cast(base_models.Counter, counter)
        next_value = counter.next_value
        counter.next_value += 1
        await counter.save()
        return next_value
