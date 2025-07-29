# tests/test_app.py

def test_home_page(test_client):
    """
    GIVEN a Flask application configured for testing
    WHEN the '/' page is requested (GET)
    THEN check that the response is valid
    """
    response = test_client.get('/')
    assert response.status_code == 200
    assert b"Welcome to the AI Platform!" in response.data
    assert b"Login" in response.data
    assert b"Register" in response.data

def test_successful_registration(test_client):
    """
    GIVEN a Flask application
    WHEN the '/register' page is posted to (POST)
    THEN check that the user is created and redirected
    """
    response = test_client.post('/register', data={
        'full_name': 'Test User',
        'email': 'test@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    }, follow_redirects=True)
    
    assert response.status_code == 200
    assert b"Your account has been created!" in response.data
    # بعد التسجيل الناجح، يجب أن يتم توجيهه إلى صفحة تسجيل الدخول
    assert b"Log In" in response.data

def test_successful_login_and_logout(test_client):
    """
    GIVEN a user has been registered
    WHEN they log in and then log out
    THEN check that the dashboard is shown and then they are logged out
    """
    # أولاً، قم بتسجيل مستخدم
    test_client.post('/register', data={
        'full_name': 'Login User',
        'email': 'login@example.com',
        'password': 'password123',
        'confirm_password': 'password123'
    })
    
    # ثانياً، قم بتسجيل الدخول
    response_login = test_client.post('/login', data={
        'email': 'login@example.com',
        'password': 'password123'
    }, follow_redirects=True)
    
    assert response_login.status_code == 200
    assert b"Welcome, Login User!" in response_login.data
    assert b"Dashboard" in response_login.data
    assert b"Logout" in response_login.data
    
    # ثالثاً، قم بتسجيل الخروج
    response_logout = test_client.get('/logout', follow_redirects=True)
    assert response_logout.status_code == 200
    assert b"Welcome to the AI Platform!" in response_logout.data
    assert b"Login" in response_logout.data