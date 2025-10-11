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

import pytest
from app.models import User, Mission, Task


class TestHealthEndpoints:
    """اختبارات نقاط الصحة - Health endpoint tests"""
    
    def test_database_health(self, client, admin_user):
        """Test database health check"""
        with client:
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': '1111'
            })
            
            response = client.get('/admin/api/database/health')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] in ['healthy', 'warning']
    
    def test_database_stats(self, client, admin_user):
        """Test database statistics"""
        with client:
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': '1111'
            })
            
            response = client.get('/admin/api/database/stats')
            assert response.status_code == 200
            data = response.get_json()
            assert 'status' in data
    
    def test_database_tables(self, client, admin_user):
        """Test list all tables"""
        with client:
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': '1111'
            })
            
            response = client.get('/admin/api/database/tables')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'
            assert 'tables' in data
            assert len(data['tables']) > 0


class TestCRUDOperations:
    """اختبارات عمليات CRUD - CRUD operations tests"""
    
    def test_create_user(self, client, admin_user, session):
        """Test creating a new user"""
        with client:
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': '1111'
            })
            
            # Create user
            user_data = {
                'email': 'newuser@example.com',
                'username': 'newuser',
                'password': 'password123'
            }
            
            response = client.post('/admin/api/database/record/users', json=user_data)
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'
            assert 'id' in data
            
            # Verify user was created
            user = User.query.filter_by(email='newuser@example.com').first()
            assert user is not None
            assert user.full_name == 'newuser'
    
    def test_read_users(self, client, admin_user, user_factory):
        """Test reading users with pagination"""
        with client:
            # Create some test users
            for i in range(5):
                user_factory(email=f'user{i}@test.com')
            
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': '1111'
            })
            
            # Read users
            response = client.get('/admin/api/database/table/users?page=1&per_page=10')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'
            assert 'rows' in data
            assert len(data['rows']) > 0
    
    def test_read_single_user(self, client, admin_user, user_factory):
        """Test reading a single user"""
        with client:
            # Create test user
            test_user = user_factory(email='testread@test.com')
            
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': '1111'
            })
            
            # Read single user
            response = client.get(f'/admin/api/database/record/users/{test_user.id}')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'
            assert data['data']['email'] == 'testread@test.com'
    
    def test_update_user(self, client, admin_user, user_factory):
        """Test updating a user"""
        with client:
            # Create test user
            test_user = user_factory(email='testupdate@test.com')
            
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': '1111'
            })
            
            # Update user
            update_data = {'full_name': 'Updated Name'}
            response = client.put(
                f'/admin/api/database/record/users/{test_user.id}',
                json=update_data
            )
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'
            
            # Verify update
            updated_user = User.query.get(test_user.id)
            assert updated_user.full_name == 'Updated Name'
    
    def test_delete_user(self, client, admin_user, user_factory, session):
        """Test deleting a user"""
        with client:
            # Create test user
            test_user = user_factory(email='testdelete@test.com')
            user_id = test_user.id
            session.commit()
            
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': '1111'
            })
            
            # Delete user
            response = client.delete(f'/admin/api/database/record/users/{user_id}')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'
            
            # Verify deletion
            deleted_user = User.query.get(user_id)
            assert deleted_user is None


class TestValidation:
    """اختبارات التحقق من صحة البيانات - Validation tests"""
    
    def test_create_user_invalid_email(self, client, admin_user):
        """Test creating user with invalid email"""
        with client:
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': '1111'
            })
            
            # Try to create user with invalid email
            user_data = {
                'email': 'not-an-email',
                'username': 'testuser',
                'password': 'password123'
            }
            
            response = client.post('/admin/api/database/record/users', json=user_data)
            # Should fail validation
            assert response.status_code in [400, 500]  # Validation or database error
    
    def test_create_user_missing_required_field(self, client, admin_user):
        """Test creating user without required fields"""
        with client:
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': '1111'
            })
            
            # Try to create user without required fields
            user_data = {
                'email': 'test@example.com'
                # Missing username and password
            }
            
            response = client.post('/admin/api/database/record/users', json=user_data)
            # Should fail
            assert response.status_code in [400, 500]


class TestPaginationAndFiltering:
    """اختبارات الترقيم والتصفية - Pagination and filtering tests"""
    
    def test_pagination(self, client, admin_user, user_factory):
        """Test pagination"""
        with client:
            # Create many users
            for i in range(25):
                user_factory(email=f'page{i}@test.com')
            
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': '1111'
            })
            
            # Get first page
            response = client.get('/admin/api/database/table/users?page=1&per_page=10')
            assert response.status_code == 200
            data = response.get_json()
            assert len(data['rows']) == 10
            assert data['page'] == 1
            
            # Get second page
            response = client.get('/admin/api/database/table/users?page=2&per_page=10')
            assert response.status_code == 200
            data = response.get_json()
            assert len(data['rows']) == 10
            assert data['page'] == 2
    
    def test_search(self, client, admin_user, user_factory):
        """Test search functionality"""
        with client:
            # Create users with specific patterns
            user_factory(email='search_test@test.com')
            user_factory(email='other@test.com')
            
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': '1111'
            })
            
            # Search for 'searchable'
            response = client.get('/admin/api/database/table/users?search=searchable')
            assert response.status_code == 200
            data = response.get_json()
            # Should find at least the searchable user
            assert any('searchable' in str(row).lower() for row in data['rows'])
    
    def test_ordering(self, client, admin_user, user_factory):
        """Test ordering"""
        with client:
            # Create users
            user1 = user_factory(email='a@test.com')
            user2 = user_factory(email='b@test.com')
            
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': '1111'
            })
            
            # Order by username ascending
            response = client.get('/admin/api/database/table/users?order_by=username&order_dir=asc')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'
            
            # Order by username descending
            response = client.get('/admin/api/database/table/users?order_by=username&order_dir=desc')
            assert response.status_code == 200
            data = response.get_json()
            assert data['status'] == 'success'


class TestErrorHandling:
    """اختبارات معالجة الأخطاء - Error handling tests"""
    
    def test_not_found_table(self, client, admin_user):
        """Test accessing non-existent table"""
        with client:
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': '1111'
            })
            
            response = client.get('/admin/api/database/table/nonexistent')
            assert response.status_code in [404, 500]
            data = response.get_json()
            assert data['status'] == 'error'
    
    def test_not_found_record(self, client, admin_user):
        """Test accessing non-existent record"""
        with client:
            # Login as admin
            client.post('/login', data={
                'email': admin_user.email,
                'password': '1111'
            })
            
            response = client.get('/admin/api/database/record/users/999999')
            assert response.status_code in [404, 500]
            data = response.get_json()
            assert data['status'] == 'error'
    
    def test_unauthorized_access(self, client):
        """Test accessing API without authentication"""
        response = client.get('/admin/api/database/tables')
        # Should redirect to login or return 401
        assert response.status_code in [302, 401]
