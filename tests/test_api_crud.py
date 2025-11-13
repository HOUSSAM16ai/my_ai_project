# tests/test_api_crud.py
import pytest
from app.models import User
from app import db

def test_crud_operations_and_health_checks(client, app, admin_user, user_factory):
    with app.app_context():
        with client:
            # Login first
            login_res = client.post("/login", data={"email": admin_user.email, "password": "password"}, follow_redirects=True)
            assert login_res.status_code == 200

            # Health Checks
            response = client.get("/admin/api/database/health")
            assert response.status_code == 200
            response = client.get("/admin/api/database/stats")
            assert response.status_code == 200
            response = client.get("/admin/api/database/tables")
            assert response.status_code == 200

            # 1. Create User via API
            user_data = {"email": "newuser@example.com", "full_name": "newuser", "password": "password123"}
            response = client.post("/admin/api/database/record/users", json=user_data)
            assert response.status_code == 200

            user = User.query.filter_by(email="newuser@example.com").first()
            assert user is not None
            user_id = user.id

            # 2. Read User
            response = client.get(f"/admin/api/database/record/users/{user_id}")
            assert response.status_code == 200
            assert response.json['data']['email'] == 'newuser@example.com'

            # 3. Update User
            update_data = {"full_name": "Updated Name"}
            response = client.put(f"/admin/api/database/record/users/{user_id}", json=update_data)
            assert response.status_code == 200

            db.session.refresh(user)
            assert user.full_name == "Updated Name"

            # 4. Delete User
            response = client.delete(f"/admin/api/database/record/users/{user_id}")
            assert response.status_code == 200

            deleted_user = User.query.get(user_id)
            assert deleted_user is None

            # 5. Test Unauthorized access after logout
            client.get("/logout", follow_redirects=True)
            response = client.get("/admin/api/database/tables")
            assert response.status_code in [302, 401]

def test_validation_and_errors(client, app, admin_user):
    with app.app_context():
        with client:
            client.post("/login", data={"email": admin_user.email, "password": "password"}, follow_redirects=True)

            # Invalid email
            user_data = {"email": "not-an-email", "full_name": "testuser", "password": "password123"}
            response = client.post("/admin/api/database/record/users", json=user_data)
            assert response.status_code in [400, 500]

            # Missing required field
            user_data = {"email": "test@example.com"}
            response = client.post("/admin/api/database/record/users", json=user_data)
            assert response.status_code in [400, 500]

            # Not found table/record
            response = client.get("/admin/api/database/table/nonexistent")
            assert response.status_code in [404, 500]
            response = client.get("/admin/api/database/record/users/999999")
            assert response.status_code in [404, 500]
