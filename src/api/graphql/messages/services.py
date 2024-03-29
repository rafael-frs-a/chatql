import typing as t
from src.api.graphql import schemas
from src.api.graphql.broadcast import broadcast
from src.api.graphql.messages import schemas as message_schemas
from src.api.graphql.messages import stores
from src.db.models import user as user_models


class MessageService:
    def __init__(self) -> None:
        self.store = stores.MessageStore()

    async def create_message(
        self, sender: user_models.User, payload: message_schemas.CreateMessageInput
    ) -> schemas.ApiResponse[message_schemas.Message]:
        if payload.channel:
            channel = payload.channel
        else:
            recipients = t.cast(list[user_models.User], payload.recipients)
            recipients += [sender]
            channel = await self.store.get_or_create_channel(recipients)

        channel_members = t.cast(list[user_models.User], channel.members)
        channel_member_ids = [member.id for member in channel_members]

        if sender.id not in channel_member_ids:
            error = schemas.ApiError(
                code=schemas.ErrorEnum.MESSAGE_SENDER_NOT_IN_CHANNEL,
                title="Sender is not part of selected channel",
            )
            return schemas.ApiResponse(errors=[error])

        message = await self.store.create_message(sender, channel, payload.content)
        await broadcast.publish(channel="messages", message=str(message.id))
        data = message_schemas.Message(message)
        return schemas.ApiResponse(data=data)
