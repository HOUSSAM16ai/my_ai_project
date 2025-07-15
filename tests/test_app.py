import pytest
from app import app as flask_app

@pytest.fixture
def app():
    yield flask_app

@pytest.fixture
def client(app):
    return app.test_client()

def test_home_page_status_code(client):
    response = client.get('/')
    assert response.status_code == 200
# استمر في نفس ملف tests/test_app.py

# ... (اترك دوال الـ fixtures 'app' و 'client' كما هي) ...

# --- الاختبار الجديد ---
def test_successful_registration(client, app):
    """
    GIVEN a Flask application configured for testing
    WHEN a new user registers with valid data
    THEN check that the user is added to the database
    """
    # استخدام app.app_context() ضروري للتفاعل مع قاعدة البيانات خارج سياق الطلب
    with app.app_context():
        # إرسال طلب POST إلى /register مع بيانات نموذج صالحة
        response = client.post('/register', data=dict(
            full_name='Test User',
            email='test@example.com',
            password='password123',
            confirm_password='password123'
        ), follow_redirects=True) # follow_redirects يتبع إعادة التوجيه بعد التسجيل

        # التأكد من أن رمز الحالة بعد إعادة التوجيه هو 200 (صفحة ناجحة)
        assert response.status_code == 200

        # التأكد من ظهور رسالة النجاح
        # ملاحظة: سنحتاج لإضافة flash messages لكود HTML لاحقًا ليعمل هذا بشكل مرئي
        assert b'Account created for Test User!' in response.data

        # التأكد من أن المستخدم تمت إضافته إلى قاعدة البيانات
        # (هذا الجزء يتطلب أن يكون لديك دالة get_db_connection في app.py)
        from app import get_db_connection
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM users WHERE email = 'test@example.com';")
        user = cur.fetchone()
        cur.close()
        conn.close()

        # التأكد من أننا وجدنا المستخدم
        assert user is not None
        # التأكد من أن اسمه صحيح
        assert user[1] == 'Test User' # بافتراض أن full_name هو العمود الثاني (id هو الأول)