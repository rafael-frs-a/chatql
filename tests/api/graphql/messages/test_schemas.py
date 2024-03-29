import pytest
from beanie import PydanticObjectId
from src.api.graphql import schemas
from src.api.graphql.messages import schemas as message_schemas
from src.db.models import user as user_models
from src.db.models import message as message_models


@pytest.mark.asyncio
async def test_create_message_input_content_missing() -> None:
    schema = message_schemas.CreateMessageInput(content="")
    error = await schema.validate_content()
    assert error
    assert error.code == schemas.ErrorEnum.FIELD_REQUIRED
    assert error.source
    assert error.source.pointer == "/content"


@pytest.mark.asyncio
@pytest.mark.parametrize("channel_id", ["", "123456789012345678901234"])
async def test_create_message_input_channel_not_found(channel_id: str) -> None:
    schema = message_schemas.CreateMessageInput(content="", channelId=channel_id)
    error = await schema.validate_channel_id()
    assert error
    assert error.code == schemas.ErrorEnum.CHANNEL_NOT_FOUND
    assert error.source
    assert error.source.pointer == "/channelId"


@pytest.mark.asyncio
@pytest.mark.parametrize("member_id", ["", "123456789012345678901234"])
async def test_create_message_input_member_not_found(member_id: str) -> None:
    schema = message_schemas.CreateMessageInput(
        content="", channelMemberIds=[member_id]
    )
    error = await schema.validate_channel_member_ids()
    assert error
    assert error.code == schemas.ErrorEnum.USER_NOT_FOUND
    assert error.source
    assert error.source.pointer == "/channelMemberIds"


@pytest.mark.asyncio
async def test_create_message_input_missing_recipient() -> None:
    schema = message_schemas.CreateMessageInput(content="")
    error = await schema.validate_recipient()
    assert error
    assert error.code == schemas.ErrorEnum.FIELD_REQUIRED
    assert error.source
    assert error.source.pointer == "/channelId"


@pytest.mark.asyncio
async def test_create_message_input_valid(jon_channel: message_models.Channel) -> None:
    schema = message_schemas.CreateMessageInput(
        content="Test message", channelId=str(jon_channel.id)
    )

    errors = await schema.validate()
    assert not errors


@pytest.mark.asyncio
async def test_channel_without_prefetch(jon_channel: message_models.Channel) -> None:
    db_channel = await message_models.Channel.get(PydanticObjectId(jon_channel.id))
    assert db_channel

    with pytest.raises(RuntimeError, match="Failed to prefetch channel's members"):
        message_schemas.Channel(db_channel)


@pytest.mark.asyncio
async def test_message_without_channel_prefetch(
    jon: user_models.User, jon_channel: message_models.Channel
) -> None:
    message = message_models.Message(
        channel=jon_channel, sender=jon, content="Test message", sequence=1
    )
    message = await message.save()
    db_message = await message_models.Message.get(PydanticObjectId(message.id))
    assert db_message

    with pytest.raises(RuntimeError, match="Failed to prefetch message's channel"):
        message_schemas.Message(db_message)


@pytest.mark.asyncio
async def test_message_without_sender_prefetch(
    jon: user_models.User, jon_channel: message_models.Channel
) -> None:
    message = message_models.Message(
        channel=jon_channel, sender=jon, content="Test message", sequence=1
    )
    message = await message.save()
    db_message = await message_models.Message.get(PydanticObjectId(message.id))
    assert db_message
    db_message.channel = jon_channel

    with pytest.raises(RuntimeError, match="Failed to prefetch message's sender"):
        message_schemas.Message(db_message)
