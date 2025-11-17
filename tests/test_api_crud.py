# ======================================================================================
# ==                    API CRUD TESTS (v1.0)                                        ==
# ======================================================================================
# PRIME DIRECTIVE:
#   اختبارات شاملة للـ CRUD API - Comprehensive CRUD API tests
#   ✨ المميزات:
#   - Test all CRUD operations
#   - Test validation
#   - Test error handling
#   - Test pagination and filtering


from app.models import User


class TestHealthEndpoints:
    """اختبارات نقاط الصحة - Health endpoint tests"""

    def test_database_health(self, client, admin_user):
        """Test database health check"""
        response = client.get("/admin/api/database/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ["healthy", "warning"]

    def test_database_stats(self, client, admin_user):
        """Test database statistics"""
        response = client.get("/admin/api/database/stats")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data

    def test_database_tables(self, client, admin_user):
        """Test list all tables"""
        response = client.get("/admin/api/database/tables")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "tables" in data
        assert len(data["tables"]) > 0


class TestCRUDOperations:
    """اختبارات عمليات CRUD - CRUD operations tests"""

    def test_create_user(self, client, admin_user, db_session):
        """Test creating a new user"""
        user_data = {
            "email": "newuser@example.com",
            "full_name": "newuser",
            "password": "password123",
        }

        response = client.post("/admin/api/database/record/users", json=user_data)
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "id" in data

        # Verify user was created
        user = db_session.query(User).filter_by(email="newuser@example.com").first()
        assert user is not None
        assert user.full_name == "newuser"

    def test_read_users(self, client, admin_user, user_factory):
        """Test reading users with pagination"""
        for i in range(5):
            user_factory(email=f"user{i}@test.com")

        response = client.get("/admin/api/database/table/users?page=1&per_page=10")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert "rows" in data
        assert len(data["rows"]) > 0

    def test_read_single_user(self, client, admin_user, user_factory):
        """Test reading a single user"""
        test_user = user_factory(email="testread@test.com")

        response = client.get(f"/admin/api/database/record/users/{test_user.id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
        assert data["data"]["email"] == "testread@test.com"

    def test_update_user(self, client, admin_user, user_factory, db_session):
        """Test updating a user"""
        test_user = user_factory(email="testupdate@test.com")

        update_data = {"full_name": "Updated Name"}
        response = client.put(
            f"/admin/api/database/record/users/{test_user.id}", json=update_data
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

        # Verify update
        updated_user = db_session.get(User, test_user.id)
        assert updated_user.full_name == "Updated Name"

    def test_delete_user(self, client, admin_user, user_factory, db_session):
        """Test deleting a user"""
        test_user = user_factory(email="testdelete@test.com")
        user_id = test_user.id
        db_session.commit()

        response = client.delete(f"/admin/api/database/record/users/{user_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

        # Verify deletion
        deleted_user = db_session.get(User, user_id)
        assert deleted_user is None


class TestValidation:
    """اختبارات التحقق من صحة البيانات - Validation tests"""

    def test_create_user_invalid_email(self, client, admin_user):
        """Test creating user with invalid email"""
        user_data = {"email": "not-an-email", "full_name": "testuser", "password": "password123"}

        response = client.post("/admin/api/database/record/users", json=user_data)
        assert response.status_code in [400, 422, 500]

    def test_create_user_missing_required_field(self, client, admin_user):
        """Test creating user without required fields"""
        user_data = {
            "email": "test@example.com"
        }

        response = client.post("/admin/api/database/record/users", json=user_data)
        assert response.status_code in [400, 422, 500]


class TestPaginationAndFiltering:
    """اختبارات الترقيم والتصفية - Pagination and filtering tests"""

    def test_pagination(self, client, admin_user, user_factory):
        """Test pagination"""
        for i in range(25):
            user_factory(email=f"page{i}@test.com")

        response = client.get("/admin/api/database/table/users?page=1&per_page=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["rows"]) == 10
        assert data["page"] == 1

        response = client.get("/admin/api/database/table/users?page=2&per_page=10")
        assert response.status_code == 200
        data = response.json()
        assert len(data["rows"]) == 10
        assert data["page"] == 2

    def test_search(self, client, admin_user, user_factory):
        """Test search functionality"""
        user_factory(email="search_test@test.com", full_name="Searchable User")
        user_factory(email="other@test.com", full_name="Other User")

        response = client.get("/admin/api/database/table/users?search=searchable")
        assert response.status_code == 200
        data = response.json()
        assert any("searchable" in str(row).lower() for row in data["rows"])

    def test_ordering(self, client, admin_user, user_factory):
        """Test ordering"""
        _ = user_factory(email="a@test.com")
        _ = user_factory(email="b@test.com")

        response = client.get("/admin/api/database/table/users?order_by=full_name&order_dir=asc")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"

        response = client.get(
            "/admin/api/database/table/users?order_by=full_name&order_dir=desc"
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"


class TestErrorHandling:
    """اختبارات معالجة الأخطاء - Error handling tests"""

    def test_not_found_table(self, client, admin_user):
        """Test accessing non-existent table"""
        response = client.get("/admin/api/database/table/nonexistent")
        assert response.status_code in [404, 500]
        data = response.json()
        assert data["status"] == "error"

    def test_not_found_record(self, client, admin_user):
        """Test accessing non-existent record"""
        response = client.get("/admin/api/database/record/users/999999")
        assert response.status_code in [404, 500]
        data = response.json()
        assert data["status"] == "error"

    def test_unauthorized_access(self, client):
        """Test accessing API without authentication"""
        response = client.get("/admin/api/database/tables")
        assert response.status_code in [401, 403]
