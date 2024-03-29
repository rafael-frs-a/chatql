import typing as t
import pytest
from beanie.exceptions import RevisionIdWasChanged
from src.db.models import base as base_models
from src.db.models import user as user_models
from src.db.models import message as message_models
from src.api.graphql.messages import stores


@pytest.mark.asyncio
async def test_get_or_create_channel_create(
    jon: user_models.User, mary: user_models.User
) -> None:
    assert await message_models.Channel.find().count() == 0

    store = stores.MessageStore()
    channel = await store.get_or_create_channel([jon, mary, jon])

    assert channel.members == [jon, mary]


@pytest.mark.asyncio
async def test_get_or_create_channel_get(
    jon: user_models.User,
    mary: user_models.User,
    common_channel: message_models.Channel,
) -> None:
    store = stores.MessageStore()
    channel = await store.get_or_create_channel([jon, mary, jon])

    assert channel.id == common_channel.id
    original_members = t.cast(list[user_models.User], common_channel.members)
    channel_members = t.cast(list[user_models.User], channel.members)
    original_members.sort(key=lambda member: str(member.id))
    channel_members.sort(key=lambda member: str(member.id))
    original_member_ids = [member.id for member in original_members]
    channel_member_ids = [member.id for member in channel_members]
    assert original_member_ids == channel_member_ids


@pytest.mark.asyncio
async def test_create_message(
    jon: user_models.User, jon_channel: message_models.Channel
) -> None:
    store = stores.MessageStore()
    content = "Message to myself"
    message = await store.create_message(jon, jon_channel, content)

    assert message.sender == jon
    assert message.channel == jon_channel
    assert message.content == content

    counter = await base_models.Counter.find_one(
        base_models.Counter.type == base_models.CounterType.MESSAGE
    )
    assert counter
    assert message.sequence == counter.next_value - 1


@pytest.mark.asyncio
async def test_create_message_conflict_sequence(
    jon: user_models.User, jon_channel: message_models.Channel
) -> None:
    store = stores.MessageStore()
    content = "Message to myself"

    counter = base_models.Counter(type=base_models.CounterType.MESSAGE)
    await counter.save()

    for count in range(store.MAX_CREATE_MESSAGE_ATTEMPTS):
        message = message_models.Message(
            sender=jon, channel=jon_channel, content=content, sequence=count + 1
        )
        await message.save()

    with pytest.raises(RevisionIdWasChanged):
        await store.create_message(jon, jon_channel, content)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "limit,channel_id,sender_id,content,content_filter,last_sequence",
    [
        (10, None, None, None, None, None),  # All messages
        (10, None, "jon", None, None, None),  # All messages from Jon
        (10, "jon_channel", None, None, None, None),  # All in Jon's private channel
        (10, None, None, None, None, 1),  # All messages except 1
        (
            10,
            "mary_channel",
            None,
            None,
            None,
            None,
        ),  # All messages in Mary's private channel (zero)
        (
            10,
            "common_channel",
            "mary",
            None,
            None,
            None,
        ),  # All messages from Mary in common channel
        (
            10,
            None,
            None,
            "message myself",
            "myself",
            None,
        ),  # All messages matching `message myself`
        (
            10,
            None,
            None,
            "hi how are you",
            "How are you",
            None,
        ),  # All messages matching `hi how are you`
        (
            -1,
            "common_channel",
            "mary",
            None,
            None,
            None,
        ),  # The last message from Mary in common channel
        (10, "", "", None, None, None),  # Invalid IDs
    ],
)
async def test_get_messages(
    jon: user_models.User,
    mary: user_models.User,
    common_channel: message_models.Channel,
    jon_channel: message_models.Channel,
    mary_channel: message_models.Channel,
    limit: int,
    channel_id: t.Optional[str],
    sender_id: t.Optional[str],
    content: t.Optional[str],
    content_filter: t.Optional[str],
    last_sequence: t.Optional[int],
) -> None:
    messages: list[message_models.Message] = []

    message = await message_models.Message(
        sender=jon, channel=jon_channel, content="Message to myself", sequence=1
    ).save()
    messages.append(message)
    await message_models.Message(
        sender=mary, channel=mary_channel, content="Message to myself", sequence=2
    ).save()
    message = await message_models.Message(
        sender=mary, channel=common_channel, content="Hi Jon!", sequence=3
    ).save()
    messages.append(message)
    message = await message_models.Message(
        sender=jon, channel=common_channel, content="Hi Mary. How are you?", sequence=4
    ).save()
    messages.append(message)
    message = await message_models.Message(
        sender=mary,
        channel=common_channel,
        content="Great! Thanks for asking",
        sequence=5,
    ).save()
    messages.append(message)

    limit = min(limit, 1)
    filtered_messages = messages[:]
    filtered_messages.sort(key=lambda message: -message.sequence)

    if channel_id:
        if channel_id == "jon_channel":
            channel_id = str(jon_channel.id)
        elif channel_id == "mary_channel":
            channel_id = str(mary_channel.id)
        elif channel_id == "common_channel":
            channel_id = str(common_channel.id)

        filtered_messages = [
            message
            for message in filtered_messages
            if str(t.cast(message_models.Channel, message.channel).id) == channel_id
        ]

    if sender_id:
        if sender_id == "jon":
            sender_id = str(jon.id)
        elif sender_id == "mary":
            sender_id = str(mary.id)

        filtered_messages = [
            message
            for message in filtered_messages
            if str(t.cast(user_models.User, message.sender).id) == sender_id
        ]

    if content_filter:
        filtered_messages = [
            message
            for message in filtered_messages
            if content_filter in message.content
        ]

    if last_sequence is not None:
        filtered_messages = [
            message for message in filtered_messages if message.sequence < last_sequence
        ]

    filtered_messages = filtered_messages[:limit]
    expected_message_ids = [message.id for message in filtered_messages]
    user = await user_models.User.find_one(
        user_models.User.id == jon.id, fetch_links=True
    )
    user = t.cast(user_models.User, user)
    store = stores.MessageStore()
    db_messages = await store.get_messages(
        user=user,
        limit=limit,
        channel_id=channel_id,
        sender_id=sender_id,
        content=content,
        last_sequence=last_sequence,
    )
    db_message_ids = [message.id for message in db_messages]
    assert expected_message_ids == db_message_ids


@pytest.mark.asyncio
@pytest.mark.parametrize("message_id", ["", "123456789012345678901234"])
async def test_get_message_not_found(message_id: str) -> None:
    store = stores.MessageStore()
    message = await store.get_message(message_id, "")
    assert message is None


@pytest.mark.asyncio
async def test_message_found(
    jon: user_models.User,
    mary: user_models.User,
    common_channel: message_models.Channel,
    mary_channel: message_models.Channel,
) -> None:
    message_mary_to_jon = await message_models.Message(
        sender=mary, channel=common_channel, content="Hi Jon", sequence=1
    ).save()
    message_mary_private = await message_models.Message(
        sender=mary, channel=mary_channel, content="Message to myself", sequence=2
    ).save()

    store = stores.MessageStore()
    message = await store.get_message(str(message_mary_to_jon.id), str(jon.id))
    assert message
    assert message.id == message_mary_to_jon.id

    message = await store.get_message(str(message_mary_private.id), str(jon.id))
    assert message is None
