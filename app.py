import os
from flask import Flask, render_template, redirect, url_for, flash, request
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, ValidationError
from werkzeug.security import generate_password_hash, check_password_hash
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv
from flask_login import LoginManager, UserMixin, login_user, current_user, logout_user, login_required

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'a_very_default_secret_key')

login_manager = LoginManager(app)
login_manager.login_view = 'login'

class User(UserMixin):
    def __init__(self, id, full_name, email, password_hash, created_at=None):
        self.id = id; self.full_name = full_name; self.email = email; self.password_hash = password_hash; self.created_at = created_at

def get_db_connection():
    try:
        conn = psycopg2.connect(host="localhost", database=os.getenv("POSTGRES_DB"), user=os.getenv("POSTGRES_USER"), password=os.getenv("POSTGRES_PASSWORD"))
        return conn
    except psycopg2.OperationalError as e:
        app.logger.error(f"DATABASE CONNECTION ERROR: {e}")
        return None

@login_manager.user_loader
def load_user(user_id):
    conn = get_db_connection()
    if conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE id = %s;", (user_id,))
            user_data = cur.fetchone()
        conn.close()
        if user_data: return User(**user_data)
    return None

class RegistrationForm(FlaskForm):
    full_name = StringField('Full Name', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    confirm_password = PasswordField('Confirm Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Sign Up')

    def validate_email(self, email):
        conn = get_db_connection()
        if conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id FROM users WHERE email = %s;", (email.data,))
                user_exists = cur.fetchone()
            conn.close()
            if user_exists: raise ValidationError('That email is already in use.')

class LoginForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    password = PasswordField('Password', validators=[DataRequired()])
    submit = SubmitField('Login')

class SubmissionForm(FlaskForm):
    answer = StringField('Your Answer', validators=[DataRequired()])
    submit = SubmitField('Submit Answer')

def get_user_by_email(email):
    conn = get_db_connection()
    user = None
    if conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM users WHERE email = %s;", (email,))
            user_data = cur.fetchone()
        conn.close()
        if user_data: user = User(**user_data)
    return user

@app.route('/')
def home(): return render_template('home.html', title='Home')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated: return redirect(url_for('dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data)
        conn = get_db_connection()
        if conn:
            with conn.cursor() as cur:
                cur.execute("INSERT INTO users (full_name, email, password_hash) VALUES (%s, %s, %s)", (form.full_name.data, form.email.data, hashed_password))
            conn.commit(); conn.close()
            flash('Your account has been created!', 'success')
            return redirect(url_for('login'))
        else:
            flash('Database connection failed.', 'danger')
    return render_template('register.html', title='Register', form=form)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated: return redirect(url_for('dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = get_user_by_email(form.email.data)
        if user and check_password_hash(user.password_hash, form.password.data):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Login Unsuccessful. Please check email and password.', 'danger')
    return render_template('login.html', title='Login', form=form)

@app.route('/logout')
def logout():
    logout_user(); return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard(): return render_template('dashboard.html', title='Dashboard')

@app.route('/exercise/<int:exercise_id>', methods=['GET', 'POST'])
@login_required
def exercise_view(exercise_id):
    conn = get_db_connection()
    exercise = None
    if conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute("SELECT * FROM exercises WHERE id = %s;", (exercise_id,))
            exercise = cur.fetchone()
        conn.close()
    if not exercise:
        flash('Exercise not found.', 'danger'); return redirect(url_for('dashboard'))

    form = SubmissionForm()
    if form.validate_on_submit():
        is_correct = (form.answer.data.strip().lower() == exercise['correct_answer'].strip().lower())
        # TODO: Save submission to database
        flash('Correct!' if is_correct else f"Incorrect. The correct answer was: {exercise['correct_answer']}", 'success' if is_correct else 'danger')
        return redirect(url_for('dashboard'))
    return render_template('exercise.html', title='Exercise', exercise=exercise, form=form)
    
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
