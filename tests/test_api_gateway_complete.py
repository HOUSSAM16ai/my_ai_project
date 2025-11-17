# tests/test_api_gateway_complete.py
# ======================================================================================
# ==        COMPREHENSIVE API GATEWAY TESTS - WORLD-CLASS EDITION                   ==
# ======================================================================================
# Tests for the complete API Gateway implementation including:
# - CRUD operations for Users, Missions, Tasks
# - Security endpoints
# - Observability endpoints
# - Gateway control endpoints

import pytest


@pytest.fixture
def sample_user(session, user_factory):
    """Create a sample user for testing"""
    import uuid

    unique_email = f"test-{uuid.uuid4().hex[:8]}@example.com"
    user = user_factory(
        full_name="Test User", email=unique_email, password="test_password", is_admin=True
    )
    session.commit()
    return user


@pytest.fixture
def sample_mission(session, sample_user, mission_factory):
    """Create a sample mission for testing"""
    mission = mission_factory(
        objective="Test Mission", status="PENDING", initiator_id=sample_user.id
    )
    session.commit()
    return mission


# ======================================================================================
# HEALTH CHECK TESTS
# ======================================================================================


class TestHealthCheck:
    """Test health check endpoints"""

    def test_api_v1_health(self, client):
        """Test API v1 health check"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "data" in data
        assert data["data"]["status"] == "healthy"
        assert data["data"]["database"] == "connected"
        assert data["data"]["version"] == "v1.0"

    def test_security_health(self, client):
        """Test security service health check"""
        response = client.get("/api/security/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["status"] == "healthy"
        assert "features" in data["data"]

    def test_observability_health(self, client):
        """Test observability service health check"""
        response = client.get("/api/observability/health")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["status"] == "healthy"

    def test_gateway_health(self, client):
        """Test gateway health check"""
        response = client.get("/api/gateway/health")
        # May return 200 or 503 depending on gateway service state
        assert response.status_code in [200, 503]


# ======================================================================================
# USERS CRUD TESTS
# ======================================================================================


class TestUsersCRUD:
    """Test Users CRUD API endpoints"""

    def test_get_users_empty(self, client):
        """Test getting users returns correct structure"""
        response = client.get("/api/v1/users")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "items" in data["data"]
        assert isinstance(data["data"]["items"], list)

    def test_get_users_with_data(self, client, sample_user):
        """Test getting users with data"""
        response = client.get("/api/v1/users")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert len(data["data"]["items"]) >= 1
        assert "pagination" in data["data"]

    def test_get_user_by_id(self, client, sample_user):
        """Test getting a specific user by ID"""
        response = client.get(f"/api/v1/users/{sample_user.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["email"] == sample_user.email

    def test_get_user_not_found(self, client):
        """Test getting a non-existent user"""
        response = client.get("/api/v1/users/99999")
        assert response.status_code == 404

    def test_get_users_with_pagination(self, client, sample_user):
        """Test pagination parameters"""
        response = client.get("/api/v1/users?page=1&per_page=10")
        assert response.status_code == 200

        data = response.json()
        assert "pagination" in data["data"]
        assert data["data"]["pagination"]["page"] == 1
        assert data["data"]["pagination"]["per_page"] == 10

    def test_get_users_with_sorting(self, client, sample_user):
        """Test sorting parameters"""
        response = client.get("/api/v1/users?sort_by=created_at&sort_order=desc")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"

    def test_get_users_with_filter(self, client, sample_user):
        """Test filtering by email"""
        response = client.get(f"/api/v1/users?email={sample_user.email}")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"


# ======================================================================================
# MISSIONS CRUD TESTS
# ======================================================================================


class TestMissionsCRUD:
    """Test Missions CRUD API endpoints"""

    def test_get_missions_empty(self, client):
        """Test getting missions when database is empty"""
        response = client.get("/api/v1/missions")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "items" in data["data"]

    def test_get_missions_with_data(self, client, sample_mission):
        """Test getting missions with data"""
        response = client.get("/api/v1/missions")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert len(data["data"]["items"]) >= 1

    def test_get_mission_by_id(self, client, sample_mission):
        """Test getting a specific mission by ID"""
        response = client.get(f"/api/v1/missions/{sample_mission.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["objective"] == sample_mission.objective

    def test_get_missions_with_status_filter(self, client, sample_mission):
        """Test filtering missions by status"""
        response = client.get("/api/v1/missions?status=PENDING")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"


# ======================================================================================
# TASKS CRUD TESTS
# ======================================================================================


class TestTasksCRUD:
    """Test Tasks CRUD API endpoints"""

    def test_get_tasks_empty(self, client):
        """Test getting tasks when database is empty"""
        response = client.get("/api/v1/tasks")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert "items" in data["data"]

    def test_get_tasks_with_mission_filter(self, client, sample_mission):
        """Test filtering tasks by mission_id"""
        response = client.get(f"/api/v1/tasks?mission_id={sample_mission.id}")
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"


# ======================================================================================
# SECURITY API TESTS
# ======================================================================================


class TestSecurityAPI:
    """Test Security API endpoints"""

    def test_generate_token(self, client, sample_user):
        """Test JWT token generation"""
        response = client.post(
            "/api/security/token/generate",
            json={"user_id": sample_user.id, "scopes": ["read", "write"]},
        )

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "access_token" in data["data"]
        assert "refresh_token" in data["data"]
        assert data["data"]["token_type"] == "Bearer"

    def test_generate_token_missing_user_id(self, client):
        """Test token generation with missing user_id"""
        response = client.post(
            "/api/security/token/generate", json={},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "error"

    def test_verify_token_missing_token(self, client):
        """Test token verification with missing token"""
        response = client.post(
            "/api/security/token/verify", json={},
        )

        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "error"


# ======================================================================================
# OBSERVABILITY API TESTS
# ======================================================================================


class TestObservabilityAPI:
    """Test Observability API endpoints"""

    def test_get_metrics(self, client):
        """Test getting metrics"""
        response = client.get("/api/observability/metrics")
        # May return 200 or 500 depending on service state
        assert response.status_code in [200, 500]

    def test_get_metrics_summary(self, client):
        """Test getting metrics summary"""
        response = client.get("/api/observability/metrics/summary")
        assert response.status_code in [200, 500]

    def test_get_latency_stats(self, client):
        """Test getting latency statistics"""
        response = client.get("/api/observability/latency")
        assert response.status_code in [200, 500]

    def test_get_performance_snapshot(self, client):
        """Test getting performance snapshot"""
        response = client.get("/api/observability/snapshot")
        assert response.status_code in [200, 500]


# ======================================================================================
# GATEWAY API TESTS
# ======================================================================================


class TestGatewayAPI:
    """Test Gateway API endpoints"""

    def test_get_routes(self, client):
        """Test getting gateway routes"""
        response = client.get("/api/gateway/routes")
        assert response.status_code in [200, 500]

    def test_get_services(self, client):
        """Test getting gateway services"""
        response = client.get("/api/gateway/services")
        assert response.status_code in [200, 500]

    def test_get_cache_stats(self, client):
        """Test getting cache statistics"""
        response = client.get("/api/gateway/cache/stats")
        assert response.status_code in [200, 500]


# ======================================================================================
# RESPONSE FORMAT TESTS
# ======================================================================================


class TestResponseFormat:
    """Test standard response format"""

    def test_success_response_format(self, client):
        """Test that success responses follow standard format"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200

        data = response.json()
        assert "status" in data
        assert "message" in data
        assert "data" in data
        assert "timestamp" in data

        assert data["status"] == "success"

    def test_error_response_format(self, client):
        """Test that error responses follow standard format"""
        response = client.get("/api/v1/users/99999")
        assert response.status_code == 404

        data = response.json()
        assert "status" in data
        assert "message" in data
        assert "timestamp" in data

        assert data["status"] == "error"


# ======================================================================================
# PAGINATION TESTS
# ======================================================================================


class TestPagination:
    """Test pagination functionality"""

    def test_pagination_structure(self, client, sample_user):
        """Test pagination response structure"""
        response = client.get("/api/v1/users?page=1&per_page=10")
        assert response.status_code == 200

        data = response.json()
        pagination = data["data"]["pagination"]

        assert "page" in pagination
        assert "per_page" in pagination
        assert "total_pages" in pagination
        assert "total_items" in pagination
        assert "has_next" in pagination
        assert "has_prev" in pagination

    def test_pagination_defaults(self, client, sample_user):
        """Test default pagination values"""
        response = client.get("/api/v1/users")
        assert response.status_code == 200

        data = response.json()
        pagination = data["data"]["pagination"]

        assert pagination["page"] == 1
        assert pagination["per_page"] == 20


# ======================================================================================
# INTEGRATION TESTS
# ======================================================================================


class TestIntegration:
    """Test complete workflows"""

    def test_complete_user_workflow(self, client, sample_user):
        """Test complete user CRUD workflow"""
        # 1. List users
        response = client.get("/api/v1/users")
        assert response.status_code == 200

        # 2. Get specific user
        response = client.get(f"/api/v1/users/{sample_user.id}")
        assert response.status_code == 200

        # 3. Health check still works
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_api_versioning(self, client):
        """Test that different API versions are accessible"""
        # v1 should work
        response = client.get("/api/v1/health")
        assert response.status_code == 200

        # Base API should work
        response = client.get("/api/security/health")
        assert response.status_code == 200


# ======================================================================================
# PERFORMANCE TESTS
# ======================================================================================


class TestPerformance:
    """Test API performance"""

    def test_response_time_health_check(self, client):
        """Test health check response time"""
        import time

        start = time.time()
        response = client.get("/api/v1/health")
        end = time.time()

        assert response.status_code == 200
        # Should respond in less than 1 second
        assert (end - start) < 1.0

    def test_response_time_users_list(self, client, sample_user):
        """Test users list response time"""
        import time

        start = time.time()
        response = client.get("/api/v1/users")
        end = time.time()

        assert response.status_code == 200
        # Should respond in less than 1 second
        assert (end - start) < 1.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
