# app/routes.py - The COMPLETE Main User-Facing Blueprint v3.1
from flask import render_template, flash, redirect, url_for, Blueprint
from flask_login import current_user, login_user, logout_user, login_required

from app import db
from app.forms import LoginForm, RegistrationForm, SubmissionForm
from app.models import User, Subject, Lesson, Exercise, Submission

# Create a self-contained unit of routes named 'main'.
bp = Blueprint('main', __name__)

# --- Core Application Routes ---

@bp.route('/')
@bp.route('/home')
def home():
    return render_template('home.html', title='Home')

@bp.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard.html', title='Dashboard')

# --- User Authentication Routes ---

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(full_name=form.full_name.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You are now able to log in.', 'success')
        return redirect(url_for('main.login'))
    return render_template('register.html', title='Register', form=form)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is None or not user.check_password(form.password.data):
            flash('Login Unsuccessful. Please check email and password.', 'danger')
            return redirect(url_for('main.login'))
        login_user(user)
        return redirect(url_for('main.dashboard')) 
    return render_template('login.html', title='Login', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.home'))

# --- Content and Learning Routes ---

@bp.route('/subjects')
@login_required
def subjects_list():
    subjects = Subject.query.order_by(Subject.name).all()
    return render_template('subjects.html', title='Subjects', subjects=subjects)

@bp.route('/subjects/<int:subject_id>')
@login_required
def lessons_list(subject_id):
    subject = Subject.query.get_or_404(subject_id)
    lessons = subject.lessons.order_by(Lesson.id).all()
    return render_template('lessons_list.html', title=f"Lessons for {subject.name}", lessons=lessons, subject_name=subject.name)

@bp.route('/lessons/<int:lesson_id>')
@login_required
def lesson_detail(lesson_id):
    lesson = Lesson.query.get_or_404(lesson_id)
    return render_template('lesson_detail.html', title=lesson.title, lesson=lesson)

@bp.route('/exercise/<int:exercise_id>', methods=['GET', 'POST'])
@login_required
def exercise_view(exercise_id):
    exercise = Exercise.query.get_or_404(exercise_id)
    form = SubmissionForm()
    if form.validate_on_submit():
        student_answer = form.answer.data.strip()
        is_correct = (student_answer.lower() == exercise.correct_answer.strip().lower())
        
        submission = Submission(
            student_answer=student_answer,
            is_correct=is_correct,
            author=current_user,
            exercise=exercise
        )
        db.session.add(submission)
        db.session.commit()
        
        if is_correct:
            flash('Correct! Well done!', 'success')
        else:
            flash(f"Incorrect. The correct answer was: {exercise.correct_answer}", 'danger')
        return redirect(url_for('main.dashboard'))
        
    return render_template('exercise.html', title='Exercise', exercise=exercise, form=form)