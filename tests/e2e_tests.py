import pytest
from httpx import AsyncClient
from main import app


@pytest.fixture
async def api_client():
    """
    Create an async HTTP client for testing FastAPI endpoints.
    """
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client


class TestMessageAPIEndToEnd:
    """
    E2E tests verify the entire system works together.
    
    These are slower but catch integration issues between layers.
    """
    
    @pytest.mark.asyncio
    async def test_health_check_endpoint_returns_200(self, api_client):
        """
        Smoke Test: Verify the service is running.
        """
        response = await api_client.get("/")
        
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    @pytest.mark.asyncio
    async def test_create_message_full_workflow(self, api_client):
        """
        Happy Path E2E: Test complete message creation workflow.
        
        This verifies:
        1. Router receives request correctly
        2. Service processes business logic
        3. Repository persists data
        4. Response is formatted correctly
        """
        # Arrange
        app_id = 1
        payload = {
            "message_content": "E2E test message",
            "phone_number_id": 1
        }
        
        # Act
        response = await api_client.post(
            f"/api/messages/{app_id}",
            json=payload
        )
        
        # Assert
        assert response.status_code == 200
        
        json_response = response.json()
        assert json_response["success"] is True
        assert "message_id" in json_response["data"]
        assert isinstance(json_response["data"]["message_id"], int)
    
    @pytest.mark.asyncio
    async def test_create_message_validates_request_body(self, api_client):
        """
        E2E: Verify API validation layer works.
        """
        # Arrange - Invalid payload (missing required field)
        app_id = 1
        invalid_payload = {
            "phone_number_id": 1
            # Missing message_content
        }
        
        # Act
        response = await api_client.post(
            f"/api/messages/{app_id}",
            json=invalid_payload
        )
        
        # Assert
        assert response.status_code == 422  # Unprocessable Entity
        assert "message_content" in response.json()["detail"][0]["loc"]
    
    @pytest.mark.asyncio
    async def test_correlation_id_flows_through_system(self, api_client):
        """
        E2E: Verify observability infrastructure works end-to-end.
        
        Critical for distributed systems debugging.
        """
        # Arrange
        correlation_id = "e2e-test-correlation-123"
        
        # Act
        response = await api_client.get(
            "/",
            headers={"X-Correlation-ID": correlation_id}
        )
        
        # Assert - Response should echo back the correlation ID
        assert response.headers.get("X-Correlation-ID") == correlation_id