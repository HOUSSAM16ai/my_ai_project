import os
from flask import Flask, render_template, redirect, url_for, flash
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from werkzeug.security import generate_password_hash
import psycopg2
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a_default_secret_key_if_not_set')

# --- دالة الاتصال بقاعدة البيانات (كما هي) ---
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
        # طباعة الخطأ في سجلات Docker لتصحيح الأخطاء
        print(f"DATABASE CONNECTION ERROR: {e}")
        return None

# --- نماذج WTForms ---
class RegistrationForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password', message='Passwords must match.')])
    submit = SubmitField('Sign Up Now')

    # دالة للتحقق مما إذا كان البريد الإلكتروني مستخدمًا بالفعل
    def validate_email(self, email):
        conn = get_db_connection()
        if conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM users WHERE email = %s;", (email.data,))
            user = cur.fetchone()
            cur.close()
            conn.close()
            if user:
                raise ValidationError('That email is already in use. Please choose a different one.')

# --- مسارات (Routes) التطبيق ---
@app.route('/')
def home():
    return '<h1>Welcome to the AI Platform!</h1><p><a href="/register">Go to Registration</a></p>'

@app.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # هذا الجزء يتم تنفيذه فقط عند إرسال النموذج بنجاح
        try:
            conn = get_db_connection()
            if conn is None:
                flash('Could not connect to the database.', 'danger')
                return render_template('register.html', title='Register', form=form)

            cur = conn.cursor()
            
            # تجزئة كلمة المرور قبل حفظها
            hashed_password = generate_password_hash(form.password.data)
            
            # تنفيذ أمر INSERT
            cur.execute("INSERT INTO users (full_name, email, password_hash) VALUES (%s, %s, %s)",
                        (form.full_name.data, form.email.data, hashed_password))
            
            conn.commit() # حفظ التغييرات في قاعدة البيانات
            cur.close()
            conn.close()
            
            flash(f'Account created successfully for {form.full_name.data}!', 'success')
            return redirect(url_for('home'))
        
        except Exception as e:
            # في حالة حدوث أي خطأ آخر في قاعدة البيانات
            flash('An error occurred while creating your account.', 'danger')
            print(f"DATABASE INSERT ERROR: {e}")

    # عرض الصفحة مع النموذج (سواء كان طلب GET أو فشل التحقق من صحة النموذج)
    return render_template('register.html', title='Register', form=form)
