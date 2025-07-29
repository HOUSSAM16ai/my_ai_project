# app/models.py - Final Version with modern UTC datetimes

# --- 1. التعديل الأول: استيراد UTC ---
from datetime import datetime, UTC
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(256))
    
    # --- 2. التعديل الثاني: استخدام الطريقة الجديدة هنا ---
    # نستخدم lambda لضمان استدعاء الدالة في كل مرة يتم فيها إنشاء سجل جديد
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    
    submissions = db.relationship('Submission', backref='author', lazy='dynamic')

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.full_name}>'

# ... (كلاسات Subject, Lesson, Exercise تبقى كما هي) ...

class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    lessons = db.relationship('Lesson', backref='subject', lazy='dynamic')
    def __repr__(self):
        return f'<Subject {self.name}>'

class Lesson(db.Model):
    __tablename__ = 'lessons'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    exercises = db.relationship('Exercise', backref='lesson', lazy='dynamic')
    def __repr__(self):
        return f'<Lesson {self.title}>'

class Exercise(db.Model):
    __tablename__ = 'exercises'
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    correct_answer = db.Column(db.String(255), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    submissions = db.relationship('Submission', backref='exercise', lazy='dynamic')
    def __repr__(self):
        return f'<Exercise {self.id}>'
        
class Submission(db.Model):
    __tablename__ = 'submissions'
    id = db.Column(db.Integer, primary_key=True)
    student_answer = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    
    # --- 3. التعديل الثالث: استخدام الطريقة الجديدة هنا أيضًا ---
    submitted_at = db.Column(db.DateTime, index=True, default=lambda: datetime.now(UTC))
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False)

    def __repr__(self):
        return f'<Submission {self.id} by User {self.user_id}>'