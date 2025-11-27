from fastapi.testclient import TestClient
from unittest.mock import patch
import time
import sys
import os

# Add project root to sys.path to ensure imports work
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from main import app


def test_health_endpoint():
    # Mock the database status check to avoid connection errors/hangs
    with patch("main.postgres_db_status", return_value=True):
        with TestClient(app) as client:
            time.sleep(1)

            response = client.get("/")
            assert response.status_code == 200
            data = response.json()
            assert data.get("data").get("status") == "ok"
            assert "uptime" in data.get("data")
            assert ":" in data.get("data").get("uptime") or "day" in data.get(
                "data"
            ).get("uptime")
            print("Test passed")


if __name__ == "__main__":
    test_health_endpoint()
