import typing as t
import strawberry
from strawberry.types import Info
from src.db.models import user as user_models
from src.db.models import message as message_models
from src.api.graphql import schemas
from src.api.graphql.broadcast import broadcast
from src.api.graphql.users import schemas as user_schemas
from src.api.graphql.auth.decorators import login_required
from src.api.graphql.messages import schemas as message_schemas
from src.api.graphql.messages import services
from src.api.graphql.messages import stores


@strawberry.type
class Query:
    @strawberry.field
    @login_required
    async def get_channels(
        self, info: Info[dict[t.Any, t.Any], t.Any]
    ) -> schemas.ApiResponse[list[message_schemas.Channel]]:
        user_validator = user_schemas.UserValidator(
            userId=info.context["userId"],
            errorSource=schemas.ApiErrorSource(header="Authorization"),
        )
        errors = await user_validator.validate()

        if errors:
            return schemas.ApiResponse(errors=errors)

        user = t.cast(user_models.User, user_validator.user)
        channels = t.cast(list[message_models.Channel], user.channels)
        data = [message_schemas.Channel(channel) for channel in channels]
        data.sort(key=lambda channel: channel.id)
        return schemas.ApiResponse(data=data)

    @strawberry.field
    @login_required
    async def get_messages(
        self,
        info: Info[dict[t.Any, t.Any], t.Any],
        limit: int = 100,
        channel_id: t.Optional[str] = None,
        sender_id: t.Optional[str] = None,
        content: t.Optional[str] = None,
        last_sequence: t.Optional[int] = None,
    ) -> schemas.ApiResponse[list[message_schemas.Message]]:
        user_validator = user_schemas.UserValidator(
            userId=info.context["userId"],
            errorSource=schemas.ApiErrorSource(header="Authorization"),
        )
        errors = await user_validator.validate()

        if errors:
            return schemas.ApiResponse(errors=errors)

        user = t.cast(user_models.User, user_validator.user)
        store = stores.MessageStore()
        messages = await store.get_messages(
            user=user,
            limit=limit,
            channel_id=channel_id,
            sender_id=sender_id,
            content=content,
            last_sequence=last_sequence,
        )
        data = [message_schemas.Message(message) for message in messages]
        return schemas.ApiResponse(data=data)


@strawberry.type
class Mutation:
    @strawberry.mutation
    @login_required
    async def create_message(
        self,
        info: Info[dict[t.Any, t.Any], t.Any],
        payload: message_schemas.CreateMessageInput,
    ) -> schemas.ApiResponse[message_schemas.Message]:
        input_errors = await payload.validate()
        user_validator = user_schemas.UserValidator(
            userId=info.context["userId"],
            errorSource=schemas.ApiErrorSource(header="Authorization"),
        )
        user_errors = await user_validator.validate()
        errors = input_errors + user_errors

        if errors:
            return schemas.ApiResponse(errors=errors)

        service = services.MessageService()
        user = t.cast(user_models.User, user_validator.user)
        return await service.create_message(user, payload)


@strawberry.type
class Subscription:
    @strawberry.subscription
    @login_required
    async def new_message(
        self, info: Info[dict[t.Any, t.Any], t.Any]
    ) -> t.AsyncGenerator[message_schemas.Message, None]:
        store = stores.MessageStore()
        user_id = info.context["userId"]

        async with broadcast.subscribe(channel="messages") as subscriber:
            async for event in subscriber:
                message = await store.get_message(event.message, user_id)

                if message:
                    yield message_schemas.Message(message)
