import base64

import pytest
from httpx import ASGITransport, AsyncClient

from news_analyst_agent.agents.utils import ModelName
from news_analyst_agent.main import app

# Mock auth credentials for testing
TEST_USERNAME = "admin"
TEST_PASSWORD = "admin"

@pytest.fixture
def auth_headers():
    # Create Basic auth header
    credentials = base64.b64encode(f"{TEST_USERNAME}:{TEST_PASSWORD}".encode()).decode()
    return {"Authorization": f"Basic {credentials}"}

@pytest.mark.anyio
async def test_health():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.get("/api/health")
    assert response.status_code == 200

@pytest.mark.anyio
async def test_chat_endpoint(auth_headers):
    chat_request = {
        "messages": [
            {
                "role": "user",
                "content": "Hi"  # Using a simple greeting to keep the test fast
            }
        ],
        "model": ModelName.LLAMA_3_2,
        "stream": False
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/api/chat", json=chat_request, headers=auth_headers)

    assert response.status_code == 200

@pytest.mark.anyio
async def test_chat_endpoint_unauthorized():
    chat_request = {
        "messages": [
            {
                "role": "user",
                "content": "Hi"
            }
        ]
    }

    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as ac:
        response = await ac.post("/api/chat", json=chat_request)
    
    assert response.status_code == 401
