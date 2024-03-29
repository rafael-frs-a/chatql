import typing as t
from bson.errors import InvalidId
from beanie import PydanticObjectId
from beanie.operators import In
from beanie.exceptions import RevisionIdWasChanged
from src.api.graphql.base import stores as base_stores
from src.db.models import base as base_models
from src.db.models import user as user_models
from src.db.models import message as message_models


class MessageStore:
    MAX_CREATE_MESSAGE_ATTEMPTS = 10

    async def get_or_create_channel(
        self,
        members: list[user_models.User],
    ) -> message_models.Channel:
        seen = set()
        deduped_members: list[user_models.User] = []

        for member in members:
            if member.id in seen:
                continue

            seen.add(member.id)
            deduped_members.append(member)

        deduped_members.sort(key=lambda member: str(member.id))
        deduped_member_ids = [member.id for member in deduped_members]
        channels = (
            await message_models.Channel.find(fetch_links=True).sort("id").to_list()
        )

        for channel in channels:
            channel_members = channel.members
            channel_members.sort(key=lambda member: str(member.id))
            channel_member_ids = [member.id for member in channel_members]

            if channel_member_ids == deduped_member_ids:
                return channel

        channel = message_models.Channel(members=deduped_members)
        channel = await channel.save()
        return channel

    async def create_message(
        self, sender: user_models.User, channel: message_models.Channel, content: str
    ) -> message_models.Message:
        base_store = base_stores.BaseStore()

        for _ in range(self.MAX_CREATE_MESSAGE_ATTEMPTS):
            try:
                message_sequence = await base_store.get_counter_sequence(
                    base_models.CounterType.MESSAGE
                )
                message = message_models.Message(
                    sender=sender,
                    content=content,
                    channel=channel,
                    sequence=message_sequence,
                )
                message = await message.save()
                return message
            except (
                RevisionIdWasChanged
            ):  # Should raise if `message_sequence` conflicts with existing sequence
                pass

        raise RevisionIdWasChanged()

    async def get_message(
        self, message_id: str, user_id: str
    ) -> t.Optional[message_models.Message]:
        try:
            message = await message_models.Message.find_one(
                message_models.Message.id == PydanticObjectId(message_id),
                fetch_links=True,
            )

            if not message:
                return None

            message = t.cast(message_models.Message, message)
            channel = t.cast(message_models.Channel, message.channel)
            members = t.cast(list[user_models.User], channel.members)
            channel_members = [str(member.id) for member in members]

            if user_id in channel_members:
                return message

            return None
        except InvalidId:
            return None

    async def get_messages(
        self,
        user: user_models.User,
        limit: int,
        channel_id: t.Optional[str] = None,
        sender_id: t.Optional[str] = None,
        content: t.Optional[str] = None,
        last_sequence: t.Optional[int] = None,
    ) -> list[message_models.Message]:
        channels = t.cast(list[message_models.Channel], user.channels)
        channel_ids = [channel.id for channel in channels]
        limit = min(max(limit, 1), 100)
        filter_channel_id: t.Optional[PydanticObjectId] = None
        filter_sender_id: t.Optional[PydanticObjectId] = None

        if channel_id is not None:
            try:
                filter_channel_id = PydanticObjectId(channel_id)
            except InvalidId:
                pass

        if sender_id is not None:
            try:
                filter_sender_id = PydanticObjectId(sender_id)
            except InvalidId:
                pass

        messages = message_models.Message.find(
            In(message_models.Message.channel.id, channel_ids)  # type: ignore[no-untyped-call]
        ).sort(-message_models.Message.sequence)

        if last_sequence:
            messages = messages.find(message_models.Message.sequence < last_sequence)

        if filter_channel_id:
            messages = messages.find(
                message_models.Message.channel.id == filter_channel_id
            )

        if filter_sender_id:
            messages = messages.find(
                message_models.Message.sender.id == filter_sender_id
            )

        if content:
            messages = messages.find({"$text": {"$search": content}})

        messages = messages.find(fetch_links=True).limit(limit)
        return await messages.to_list()
