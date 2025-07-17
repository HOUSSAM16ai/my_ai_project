import pytest
from app import app as flask_app, get_db_connection

# --- Fixtures للاختبار ---

@pytest.fixture
def app():
    """إنشاء وتهيئة نسخة جديدة من التطبيق لكل اختبار."""
    # 1. تحديث إعدادات التطبيق لوضع الاختبار
    flask_app.config.update({
        "TESTING": True,
        "WTF_CSRF_ENABLED": False,
    })

    # 2. تهيئة قاعدة البيانات قبل كل اختبار
    with flask_app.app_context():
        conn = get_db_connection()
        with conn.cursor() as cur:
            # حذف الجداول بالترتيب الصحيح لتجنب أخطاء المفتاح الأجنبي
            cur.execute("DROP TABLE IF EXISTS lessons, users, subjects CASCADE;")
            
            # إعادة إنشاء الجداول
            cur.execute("""
                CREATE TABLE subjects (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) UNIQUE NOT NULL,
                    description TEXT
                );
            """)
            cur.execute("""
                CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    full_name VARCHAR(100) NOT NULL,
                    email VARCHAR(120) UNIQUE NOT NULL,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """)
            cur.execute("""
                CREATE TABLE lessons (
                    id SERIAL PRIMARY KEY,
                    title VARCHAR(255) NOT NULL,
                    content TEXT NOT NULL,
                    subject_id INTEGER NOT NULL,
                    CONSTRAINT fk_subject
                        FOREIGN KEY(subject_id) 
                        REFERENCES subjects(id)
                        ON DELETE CASCADE
                );
            """)
            
            # إضافة بيانات تجريبية
            cur.execute("INSERT INTO subjects (id, name, description) VALUES (1, 'الرياضيات', 'وصف الرياضيات');")
            cur.execute("INSERT INTO lessons (title, content, subject_id) VALUES ('الدالة الأسية', 'محتوى الدرس...', 1);")
        conn.commit()
        conn.close()

    # 3. إرجاع كائن التطبيق المهيأ
    yield flask_app


@pytest.fixture
def client(app):
    """Fixture لعميل اختبار Flask."""
    return app.test_client()

# --- مجموعة اختبارات المصادقة (Authentication) ---
class TestAuth:

    def test_home_page_for_anonymous_user(self, client):
        """اختبار الصفحة الرئيسية للمستخدم غير المسجل."""
        response = client.get('/')
        assert response.status_code == 200
        response_text = response.data.decode('utf-8')
        assert "Welcome to the AI Platform!" in response_text
        assert "Please log in or register to continue." in response_text

    def test_registration_page_loads(self, client):
        """اختبار أن صفحة التسجيل تفتح بنجاح."""
        response = client.get('/register')
        assert response.status_code == 200
        assert "Create Your Account" in response.data.decode('utf-8')

    def test_successful_registration(self, client, app):
        """اختبار أن التسجيل الناجح يضيف مستخدمًا لقاعدة البيانات."""
        client.post('/register', data=dict(
            full_name='Test User',
            email='test@example.com',
            password='password123',
            confirm_password='password123'
        ))
        
        # التحقق من قاعدة البيانات
        with app.app_context():
            conn = get_db_connection()
            with conn.cursor() as cur:
                cur.execute("SELECT * FROM users WHERE email = 'test@example.com';")
                user = cur.fetchone()
            conn.close()
            assert user is not None

    def test_duplicate_email_registration_fails(self, client):
        """اختبار أن التسجيل بنفس البريد الإلكتروني مرة أخرى يفشل."""
        client.post('/register', data=dict(full_name='First User', email='duplicate@example.com', password='p1', confirm_password='p1'))
        response = client.post('/register', data=dict(full_name='Second User', email='duplicate@example.com', password='p2', confirm_password='p2'))
        assert "That email is already in use." in response.data.decode('utf-8')

    def test_successful_login_and_logout(self, client):
        """اختبار تسجيل الدخول، رؤية لوحة التحكم، ثم تسجيل الخروج."""
        client.post('/register', data=dict(full_name='Login User', email='login@example.com', password='p123', confirm_password='p123'))
        
        response_login = client.post('/login', data=dict(email='login@example.com', password='p123'), follow_redirects=True)
        assert response_login.status_code == 200
        assert 'Welcome to your Dashboard' in response_login.data.decode('utf-8')

        response_logout = client.get('/logout', follow_redirects=True)
        assert response_logout.status_code == 200
        assert "Login" in response_logout.data.decode('utf-8')

    def test_login_with_wrong_password_fails(self, client):
        """اختبار أن تسجيل الدخول بكلمة مرور خاطئة يفشل."""
        client.post('/register', data=dict(full_name='Wrong Pass User', email='wrongpass@example.com', password='correctpassword', confirm_password='correctpassword'))
        response = client.post('/login', data=dict(email='wrongpass@example.com', password='wrongpassword'))
        assert "Login Unsuccessful." in response.data.decode('utf-8')
        
    def test_accessing_protected_page_without_login(self, client):
        """اختبار أن المستخدم غير المسجل يتم إعادة توجيهه عند محاولة الوصول لـ /dashboard."""
        response = client.get('/dashboard', follow_redirects=True)
        assert response.status_code == 200
        assert "Please log in to access this page." in response.data.decode('utf-8')


# --- مجموعة اختبارات المحتوى التعليمي (Content) ---
class TestContent:
    @pytest.fixture(autouse=True)
    def logged_in_client(self, client):
        """Fixture يقوم بتسجيل دخول مستخدم تلقائيًا لكل اختبار في هذا الكلاس."""
        client.post('/register', data=dict(full_name='Content Tester', email='content@test.com', password='p', confirm_password='p'))
        client.post('/login', data=dict(email='content@test.com', password='p'))
        return client

    def test_subjects_page_loads_for_logged_in_user(self, logged_in_client):
        """اختبار أن المستخدم المسجل يرى قائمة المواد."""
        response = logged_in_client.get('/subjects')
        assert response.status_code == 200
        assert "Available Subjects" in response.data.decode('utf-8')
        assert "الرياضيات" in response.data.decode('utf-8')

    def test_lessons_list_page_loads(self, logged_in_client):
        """اختبار أن المستخدم المسجل يرى قائمة الدروس لمادة معينة."""
        response = logged_in_client.get('/subjects/1') # مادة الرياضيات (id=1)
        assert response.status_code == 200
        assert "Lessons for: الرياضيات" in response.data.decode('utf-8')
        assert "الدالة الأسية" in response.data.decode('utf-8')