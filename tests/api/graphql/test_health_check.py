from fastapi import status
from fastapi.testclient import TestClient


def test_success(client: TestClient) -> None:
    query = """
        query TestQuery {
            healthCheck {
                success
            }
        }
    """
    response = client.post("/graphql", json={"query": query})
    assert response.status_code == status.HTTP_200_OK
    response_json = response.json()
    assert "errors" not in response_json
    response_data = response_json["data"]["healthCheck"]
    assert response_data["success"] is True
