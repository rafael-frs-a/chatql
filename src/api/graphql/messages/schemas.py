import typing as t
import strawberry
from datetime import datetime
from beanie import PydanticObjectId
from bson.errors import InvalidId
from src.api.graphql import schemas
from src.api.graphql.users import schemas as user_schemas
from src.db.models import user as user_models
from src.db.models import message as message_models


@strawberry.input
class CreateMessageInput(schemas.ApiInput):
    content: str
    channelId: t.Optional[str] = None
    channelMemberIds: t.Optional[list[str]] = None
    channel: strawberry.Private[t.Optional[message_models.Channel]] = None
    recipients: strawberry.Private[t.Optional[list[user_models.User]]] = None

    async def validate_content(self) -> t.Optional[schemas.ApiError]:
        if not self.content:
            return schemas.ApiError(
                code=schemas.ErrorEnum.FIELD_REQUIRED,
                title="Message content required",
                source=schemas.ApiErrorSource(pointer="/content"),
            )

        return None

    async def validate_channel_id(self) -> t.Optional[schemas.ApiError]:
        try:
            self.channel = await message_models.Channel.find_one(
                message_models.Channel.id == PydanticObjectId(self.channelId),
                fetch_links=True,
            )
        except InvalidId:
            pass

        if not self.channel:
            return schemas.ApiError(
                code=schemas.ErrorEnum.CHANNEL_NOT_FOUND,
                title="Channel not found",
                source=schemas.ApiErrorSource(pointer="/channelId"),
            )

        return None

    async def validate_channel_member_ids(self) -> t.Optional[schemas.ApiError]:
        self.channelMemberIds = self.channelMemberIds or []
        self.recipients = []

        for user_id in self.channelMemberIds:
            recipient: t.Optional[user_models.User] = None

            try:
                recipient = await user_models.User.get(PydanticObjectId(user_id))
            except InvalidId:
                pass

            if not recipient:
                return schemas.ApiError(
                    code=schemas.ErrorEnum.USER_NOT_FOUND,
                    title="Recipient user not found",
                    source=schemas.ApiErrorSource(pointer="/channelMemberIds"),
                )

            self.recipients.append(recipient)

        return None

    async def validate_recipient(self) -> t.Optional[schemas.ApiError]:
        if self.channelId:
            return await self.validate_channel_id()

        if self.channelMemberIds:
            return await self.validate_channel_member_ids()

        return schemas.ApiError(
            code=schemas.ErrorEnum.FIELD_REQUIRED,
            title="Recipient required",
            source=schemas.ApiErrorSource(pointer="/channelId"),
        )

    async def validate(self) -> list[schemas.ApiError]:
        content_error = await self.validate_content()
        recipient_error = await self.validate_recipient()
        errors = [content_error, recipient_error]
        filtered_errors = [_ for _ in errors if _]
        return filtered_errors


@strawberry.type
class Channel:
    id: str
    createdAt: datetime
    updatedAt: datetime
    members: list[user_schemas.User]

    def __init__(self, channel: message_models.Channel) -> None:
        self.id = str(channel.id)
        self.createdAt = channel.created_at
        self.updatedAt = channel.updated_at
        self.members = []

        for member in channel.members:
            if not isinstance(member, user_models.User):
                raise RuntimeError("Failed to prefetch channel's members")

            user = t.cast(user_models.User, member)
            self.members.append(user_schemas.User(user))

        self.members.sort(key=lambda member: member.id)


@strawberry.type
class Message:
    id: str
    createdAt: datetime
    updatedAt: datetime
    channel: Channel
    sender: user_schemas.User
    content: str
    sequence: int

    def __init__(self, message: message_models.Message) -> None:
        self.id = str(message.id)
        self.content = message.content
        self.createdAt = message.created_at
        self.updatedAt = message.updated_at
        self.sequence = message.sequence

        if not isinstance(message.channel, message_models.Channel):
            raise RuntimeError("Failed to prefetch message's channel")

        channel = t.cast(message_models.Channel, message.channel)
        self.channel = Channel(channel)

        if not isinstance(message.sender, user_models.User):
            raise RuntimeError("Failed to prefetch message's sender")

        sender = t.cast(user_models.User, message.sender)
        self.sender = user_schemas.User(sender)
