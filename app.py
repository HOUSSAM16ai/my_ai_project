import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required

# --- نموذج المستخدم (يجب أن يكون متاحًا عالميًا لـ user_loader) ---
class User(UserMixin):
    def __init__(self, id, full_name, email, password_hash, created_at=None):
        self.id = id
        self.full_name = full_name
        self.email = email
        self.password_hash = password_hash
        self.created_at = created_at

# --- دوال قاعدة البيانات (تعتبر دوال مساعدة) ---
def get_db_connection():
    try:
        conn = psycopg2.connect(
            host="db",
            database=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD")
        )
        return conn
    except psycopg2.OperationalError as e:
        print(f"DATABASE CONNECTION ERROR: {e}")
        return None

def get_user_by_email(email):
    conn = get_db_connection()
    user = None
    if conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE email = %s;", (email,))
            user_data = cur.fetchone()
        conn.close()
        if user_data:
            user = User(**user_data)
    return user

def get_user_by_id(user_id):
    conn = get_db_connection()
    user = None
    if conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE id = %s;", (user_id,))
            user_data = cur.fetchone()
        conn.close()
        if user_data:
            user = User(**user_data)
    return user

# --- الدالة الرئيسية لإنشاء التطبيق (Application Factory) ---
def create_app(config_name='development'):
    load_dotenv()
    app = Flask(__name__)
    
    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a_very_default_secret_key')
    if config_name == 'testing':
        app.config['TESTING'] = True
        app.config['WTF_CSRF_ENABLED'] = False
    
    # --- إعداد Flask-Login ---
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'login'
    login_manager.login_message_category = 'info'
    login_manager.login_message = "Please log in to access this page."

    @login_manager.user_loader
    def load_user(user_id):
        return get_user_by_id(user_id)

    # --- نماذج WTForms ---
    class RegistrationForm(FlaskForm):
        full_name = StringField('Full Name', validators=[DataRequired()])
        email = StringField('Email', validators=[DataRequired(), Email()])
        password = PasswordField('Password', validators=[DataRequired()])
        confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
        submit = SubmitField('Sign Up')

        def validate_email(self, email):
            if get_user_by_email(email.data):
                raise ValidationError('That email is already in use. Please choose a different one.')

    class LoginForm(FlaskForm):
        email = StringField('Email', validators=[DataRequired(), Email()])
        password = PasswordField('Password', validators=[DataRequired()])
        submit = SubmitField('Login')

    # --- مسارات (Routes) التطبيق ---
    @app.route('/')
    @app.route('/home')
    def home():
        return render_template('home.html', title='Home')

    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if current_user.is_authenticated:
            return redirect(url_for('home'))
        form = RegistrationForm()
        if form.validate_on_submit():
            hashed_password = generate_password_hash(form.password.data)
            conn = get_db_connection()
            if conn:
                with conn.cursor() as cur:
                    cur.execute("INSERT INTO users (full_name, email, password_hash) VALUES (%s, %s, %s)",
                                (form.full_name.data, form.email.data, hashed_password))
                conn.commit()
                conn.close()
                flash('Your account has been created! You are now able to log in.', 'success')
                return redirect(url_for('login'))
            else:
                flash('Database connection failed.', 'danger')
        return render_template('register.html', title='Register', form=form)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if current_user.is_authenticated:
            return redirect(url_for('home'))
        form = LoginForm()
        if form.validate_on_submit():
            user = get_user_by_email(form.email.data)
            if user and check_password_hash(user.password_hash, form.password.data):
                login_user(user)
                next_page = request.args.get('next')
                flash('You have been logged in successfully!', 'success')
                return redirect(next_page) if next_page else redirect(url_for('dashboard'))
            else:
                flash('Login Unsuccessful. Please check email and password.', 'danger')
        return render_template('login.html', title='Login', form=form)

    @app.route('/logout')
    @login_required
    def logout():
        logout_user()
        return redirect(url_for('home'))

    @app.route('/dashboard')
    @login_required
    def dashboard():
        return f"<h1>Welcome to your Dashboard, {current_user.full_name}!</h1>"
        
    return app

# هذا الجزء مخصص فقط للتشغيل المحلي المباشر خارج Docker
if __name__ == '__main__':
    app = create_app()
    app.run(host='0.0.0.0', port=5000, debug=True)
