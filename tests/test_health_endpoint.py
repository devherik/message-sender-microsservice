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
            # Wait a bit to ensure uptime is non-zero
            time.sleep(1)

            response = client.get("/health")
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "ok"
            assert "uptime" in data
            # Check for timedelta format (e.g., "0:00:01" or "1 day, ...")
            assert ":" in data["uptime"] or "day" in data["uptime"]
