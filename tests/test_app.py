import pytest
from app import create_app, get_db_connection

# --- Fixtures للاختبار ---
# هذه دوال إعدادية تعمل قبل كل اختبار يستخدمها
@pytest.fixture
def app():
    """إنشاء وتهيئة نسخة جديدة من التطبيق لكل اختبار."""
    app = create_app('testing')
    
    # تهيئة قاعدة البيانات قبل كل اختبار
    # هذا يضمن أن كل اختبار يبدأ من قاعدة بيانات نظيفة
    with app.app_context():
        conn = get_db_connection()
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS users;") # حذف الجدول القديم لضمان النظافة
            cur.execute("""
                CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    full_name VARCHAR(100) NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
        conn.commit()
        conn.close()

    yield app

@pytest.fixture
def client(app):
    """Fixture لعميل اختبار Flask."""
    return app.test_client()

# --- مجموعة اختبارات المصادقة (Authentication) ---
# استخدام الكلاس لتنظيم الاختبارات المتعلقة بنفس الموضوع
class TestAuth:

    def test_home_page(self, client):
        """
        السيناريو: مستخدم يزور الصفحة الرئيسية.
        النتيجة المتوقعة: تفتح الصفحة بنجاح (رمز 200).
        """
        response = client.get('/')
        assert response.status_code == 200
        assert b"Welcome to the AI Platform!" in response.data

    def test_registration_page(self, client):
        """
        السيناريو: مستخدم يزور صفحة التسجيل.
        النتيجة المتوقعة: تفتح الصفحة بنجاح (رمز 200) وتعرض نموذج التسجيل.
        """
        response = client.get('/register')
        assert response.status_code == 200
        assert b"Create Your Account" in response.data

    def test_successful_registration_and_redirect(self, client):
        """
        السيناريو: مستخدم يرسل بيانات تسجيل صالحة.
        النتيجة المتوقعة: يتم إنشاء الحساب، تظهر رسالة نجاح، ويتم إعادة توجيهه لصفحة تسجيل الدخول.
        """
        response = client.post('/register', data=dict(
            full_name='Test User',
            email='test@example.com',
            password='password123',
            confirm_password='password123'
        ), follow_redirects=True) # follow_redirects مهم لتتبع إعادة التوجيه
        
        assert response.status_code == 200 # بعد إعادة التوجيه، يجب أن تكون صفحة تسجيل الدخول ناجحة
        assert b"Your account has been created!" in response.data
        assert b"Login" in response.data # يجب أن يرى الآن نموذج تسجيل الدخول

    def test_duplicate_email_registration_fails(self, client):
        """
        السيناريو: مستخدم يحاول التسجيل ببريد إلكتروني مستخدم بالفعل.
        النتيجة المتوقعة: تبقى في صفحة التسجيل وتظهر رسالة خطأ.
        """
        # تسجيل المستخدم الأول
        client.post('/register', data=dict(full_name='First User', email='duplicate@example.com', password='p1', confirm_password='p1'))
        
        # محاولة التسجيل مرة أخرى بنفس البريد
        response = client.post('/register', data=dict(full_name='Second User', email='duplicate@example.com', password='p2', confirm_password='p2'))
        
        assert response.status_code == 200
        assert b'That email is already in use.' in response.data

    def test_successful_login_and_logout(self, client):
        """
        السيناريو: مستخدم مسجل يقوم بتسجيل الدخول ثم تسجيل الخروج.
        النتيجة المتوقعة: يتم توجيهه للوحة التحكم ثم إلى الصفحة الرئيسية.
        """
        # أولاً، أنشئ مستخدمًا
        client.post('/register', data=dict(full_name='Login User', email='login@example.com', password='password123', confirm_password='password123'))

        # الآن، حاول تسجيل الدخول
        response_login = client.post('/login', data=dict(
            email='login@example.com',
            password='password123'
        ), follow_redirects=True)
        
        assert response_login.status_code == 200
        assert b'Welcome to your Dashboard, Login User!' in response_login.data # يجب أن يرى لوحة التحكم

        # الآن، حاول تسجيل الخروج
        response_logout = client.get('/logout', follow_redirects=True)
        assert response_logout.status_code == 200
        assert b"Login" in response_logout.data # رابط تسجيل الدخول يجب أن يظهر مرة أخرى

    def test_login_with_wrong_password_fails(self, client):
        """
        السيناريو: مستخدم مسجل يحاول تسجيل الدخول بكلمة مرور خاطئة.
        النتيجة المتوقعة: تبقى في صفحة تسجيل الدخول وتظهر رسالة خطأ.
        """
        # أنشئ مستخدمًا
        client.post('/register', data=dict(full_name='Wrong Pass User', email='wrongpass@example.com', password='correctpassword', confirm_password='correctpassword'))
        
        # حاول تسجيل الدخول بكلمة مرور خاطئة
        response = client.post('/login', data=dict(
            email='wrongpass@example.com',
            password='wrongpassword'
        ))
        
        assert response.status_code == 200
        assert b'Login Unsuccessful. Please check email and password.' in response.data

    def test_accessing_protected_page_without_login(self, client):
        """
        السيناريو: مستخدم غير مسجل يحاول الوصول لصفحة محمية (/dashboard).
        النتيجة المتوقعة: يتم إعادة توجيهه لصفحة تسجيل الدخول.
        """
        response = client.get('/dashboard', follow_redirects=True)
        assert response.status_code == 200
        assert b"Please log in to access this page." in response.data
        assert b"Login" in response.data