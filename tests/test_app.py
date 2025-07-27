import pytest
import os
import psycopg2
from app import app as flask_app, get_db_connection
from psycopg2.extras import RealDictCursor

@pytest.fixture
def app():
    # We now set the config variables directly on the app object
    # This is cleaner and more reliable than setting os.environ
    flask_app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
        "SECRET_KEY": "a_test_secret",
        "POSTGRES_HOST": "localhost",
        "POSTGRES_DB": "mydb_test",
        "POSTGRES_USER": "user",
        "POSTGRES_PASSWORD": "password"
    })

    with flask_app.app_context():
        # Connect to the maintenance db to create the test db
        conn_maint = psycopg2.connect(
            host=flask_app.config["POSTGRES_HOST"],
            user=flask_app.config["POSTGRES_USER"],
            password=flask_app.config["POSTGRES_PASSWORD"],
            dbname="postgres"
        )
        conn_maint.autocommit = True
        with conn_maint.cursor() as cur:
            cur.execute(f"DROP DATABASE IF EXISTS {flask_app.config['POSTGRES_DB']} WITH (FORCE);")
            cur.execute(f"CREATE DATABASE {flask_app.config['POSTGRES_DB']};")
        conn_maint.close()

        # Connect to the new test db to apply the schema
        conn = get_db_connection()
        assert conn is not None, "Failed to connect to the test database."
        with conn.cursor() as cur:
            with open('schema.sql', 'r', encoding='utf-8') as f:
                cur.execute(f.read())
        conn.commit()
        conn.close()
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

# --- All test classes and functions below this line remain the same ---
class TestAuth:
    def test_home_page_for_anonymous_user(self, client):
        response = client.get('/')
        assert response.status_code == 200
        assert b"Welcome to the AI Platform!" in response.data
    def test_registration_page_loads(self, client):
        response = client.get('/register')
        assert response.status_code == 200
        assert b"Sign Up" in response.data
    def test_successful_registration_and_login(self, client, app):
        reg_response = client.post('/register', data={'full_name': 'Test User','email': 'test@example.com','password': 'password123','confirm_password': 'password123'}, follow_redirects=True)
        assert b"Your account has been created!" in reg_response.data
        login_response = client.post('/login', data={'email': 'test@example.com', 'password': 'password123'}, follow_redirects=True)
        assert b"Welcome to your Dashboard" in login_response.data
    def test_duplicate_email_registration_fails(self, client):
        client.post('/register', data={'full_name': 'First', 'email': 'duplicate@example.com', 'password': 'p1', 'confirm_password': 'p1'})
        response = client.post('/register', data={'full_name': 'Second', 'email': 'duplicate@example.com', 'password': 'p2', 'confirm_password': 'p2'})
        assert b"That email is already in use." in response.data
    def test_accessing_protected_page_without_login(self, client):
        response = client.get('/dashboard', follow_redirects=True)
        assert b"Login" in response.data

class TestContent:
    @pytest.fixture(autouse=True)
    def logged_in_client(self, client):
        client.post('/register', data={'full_name': 'Content Tester', 'email': 'content@test.com', 'password': 'p', 'confirm_password': 'p'})
        client.post('/login', data={'email': 'content@test.com', 'password': 'p'})
        return client
    def test_subjects_page_loads(self, logged_in_client):
        response = logged_in_client.get('/subjects')
        assert response.status_code == 200
        response_text = response.data.decode('utf-8')
        assert "Subjects" in response_text
        assert "الرياضيات" in response_text
    def test_exercise_page_loads(self, logged_in_client):
        response = logged_in_client.get('/exercise/1')
        assert response.status_code == 200
        response_text = response.data.decode('utf-8')
        assert "ما هو ناتج 5 * 5 ؟" in response_text
    def test_exercise_submission_is_saved_in_db(self, logged_in_client, app):
        response = logged_in_client.post('/exercise/1', data={'answer': '25'}, follow_redirects=True)
        assert response.status_code == 200
        response_text = response.data.decode('utf-8')
        assert 'Your answer has been submitted!' in response_text
        assert 'Correct! Well done!' in response_text
        with app.app_context():
            conn = get_db_connection()
            submission = None
            if conn:
                with conn.cursor(cursor_factory=RealDictCursor) as cur:
                    cur.execute("SELECT id FROM users WHERE email = 'content@test.com';")
                    user = cur.fetchone()
                    assert user is not None, "Test user 'content@test.com' was not found."
                    user_id = user['id']
                    cur.execute("SELECT * FROM submissions WHERE user_id = %s AND exercise_id = 1;", (user_id,))
                    submission = cur.fetchone()
                conn.close()
        assert submission is not None, "Submission was not found in the database!"
        assert submission['student_answer'] == '25'
        assert submission['is_correct'] is True