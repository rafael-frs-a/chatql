import typing as t
import pytest
from contextlib import asynccontextmanager
from broadcaster._base import Event
from starlette.requests import Request
from fastapi.testclient import TestClient
from strawberry.subscriptions import GRAPHQL_WS_PROTOCOL
from src.app import app
from src.api.graphql import schema
from src.api.graphql.broadcast import broadcast
from src.db.models.user import User
from src.db.models.message import Channel, Message


class MockSubscriber:
    def __init__(self, event: Event) -> None:
        self.event = event

    async def __aiter__(self) -> t.AsyncGenerator[Event, None]:
        yield self.event


@pytest.mark.asyncio
async def test_success(
    jon_token: str, mary: User, common_channel: Channel, monkeypatch: pytest.MonkeyPatch
) -> None:
    query = """
        subscription TestSubscription {
            newMessage {
                id
            }
        }
    """
    message = await Message(
        channel=common_channel, sender=mary, content="Hi Jon!", sequence=1
    ).save()

    @asynccontextmanager
    async def mock_subscribe(
        *args: list[t.Any], **kwargs: dict[t.Any, t.Any]
    ) -> t.AsyncGenerator[MockSubscriber, None]:
        event = Event(channel="messages", message=str(message.id))
        yield MockSubscriber(event)

    monkeypatch.setattr(broadcast, "subscribe", mock_subscribe)

    token = f"Bearer {jon_token}"
    headers = {"Authorization": token}
    scope = {
        "type": "http",
        "headers": [
            [b"authorization", token.encode()],
        ],
    }
    scope.update({"type": "http"})
    request = Request(scope=scope)
    sub = await schema.subscribe(query, context_value={"request": request})

    async for result in sub:  # type: ignore[union-attr]
        data = t.cast(dict[str, t.Any], result.data)
        assert data["newMessage"]["id"] == str(message.id)
        assert not result.errors

    with TestClient(app) as client:
        with client.websocket_connect(
            "/graphql", headers=headers, subprotocols=[GRAPHQL_WS_PROTOCOL]
        ) as ws:
            ws.send_json({"type": "connection_init"})
            response = ws.receive_json()
            assert response == {"type": "connection_ack"}

            ws.send_json({"id": "1", "type": "start", "payload": {"query": query}})
            response = ws.receive_json()
            assert response == {
                "type": "data",
                "id": "1",
                "payload": {"data": {"newMessage": {"id": str(message.id)}}},
            }
