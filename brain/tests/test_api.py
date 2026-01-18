"""
Tests for FastAPI gateway.
"""

import pytest
from fastapi.testclient import TestClient
from api.main import app

client = TestClient(app)


class TestHealthEndpoints:
    """Test health and status endpoints."""

    def test_root_endpoint(self):
        """Test root endpoint."""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert data["service"] == "Vanguard AI Agent Gateway"
        assert data["status"] == "running"

    def test_health_check(self):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "components" in data
        assert data["components"]["workflow"] == "healthy"

    def test_stats_endpoint(self):
        """Test stats endpoint."""
        response = client.get("/stats")
        assert response.status_code == 200
        data = response.json()
        assert "total_workflows" in data
        assert "pending_workflows" in data
        assert "completed_workflows" in data


class TestWorkflowEndpoints:
    """Test workflow trigger and status endpoints."""

    def test_trigger_workflow(self):
        """Test triggering a workflow."""
        payload = {
            "event_type": "LOW_INVENTORY",
            "machine_id": "INVENTORY-SYSTEM",
            "severity": "MEDIUM",
            "description": "Test low inventory event",
            "metadata": {
                "part_name": "BEARING_6205",
                "current_stock": 5,
                "minimum_stock": 10,
            },
        }

        response = client.post("/workflows/trigger", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert "job_id" in data
        assert data["status"] == "pending"
        assert "event_id" in data

        # Save job_id for next test
        return data["job_id"]

    def test_get_workflow_status(self):
        """Test getting workflow status."""
        # First create a workflow
        job_id = self.test_trigger_workflow()

        # Get status
        response = client.get(f"/workflows/{job_id}")
        assert response.status_code == 200

        data = response.json()
        assert data["job_id"] == job_id
        assert "status" in data

    def test_get_nonexistent_workflow(self):
        """Test getting status of non-existent workflow."""
        response = client.get("/workflows/nonexistent-job-id")
        assert response.status_code == 404

    def test_list_workflows(self):
        """Test listing workflows."""
        response = client.get("/workflows")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)

    def test_list_workflows_with_filter(self):
        """Test listing workflows with status filter."""
        response = client.get("/workflows?status=completed&limit=10")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, list)


class TestValidation:
    """Test request validation."""

    def test_trigger_workflow_missing_fields(self):
        """Test that missing required fields are rejected."""
        payload = {
            "event_type": "LOW_INVENTORY"
            # Missing machine_id and description
        }

        response = client.post("/workflows/trigger", json=payload)
        assert response.status_code == 422  # Validation error

    def test_trigger_workflow_invalid_event_type(self):
        """Test that invalid event types are rejected."""
        payload = {
            "event_type": "INVALID_TYPE",
            "machine_id": "TEST",
            "description": "Test",
        }

        response = client.post("/workflows/trigger", json=payload)
        assert response.status_code == 422

    def test_list_workflows_invalid_limit(self):
        """Test that invalid limits are rejected."""
        response = client.get("/workflows?limit=0")
        assert response.status_code == 422

        response = client.get("/workflows?limit=10000")
        assert response.status_code == 422
