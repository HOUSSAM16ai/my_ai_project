# app/models.py - The Self-Learning Akashic Records (Wisdom Engine Enabled)

import uuid
from datetime import datetime, UTC
from app import db, login_manager
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    """Loads a user from the database for Flask-Login."""
    return db.session.get(User, int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    email = db.Column(db.String(150), unique=True, index=True, nullable=False)
    password_hash = db.Column(db.String(256))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(UTC))
    is_admin = db.Column(db.Boolean, nullable=False, default=False, server_default='f')
    
    submissions = db.relationship('Submission', backref='author', lazy='dynamic', cascade="all, delete-orphan")
    conversations = db.relationship('Conversation', backref='user', lazy='dynamic', cascade="all, delete-orphan")

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.full_name}>'

# --- Educational Core Models ---

class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    lessons = db.relationship('Lesson', backref='subject', lazy='dynamic', cascade="all, delete-orphan")
    def __repr__(self):
        return f'<Subject {self.name}>'

class Lesson(db.Model):
    __tablename__ = 'lessons'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    subject_id = db.Column(db.Integer, db.ForeignKey('subjects.id'), nullable=False)
    exercises = db.relationship('Exercise', backref='lesson', lazy='dynamic', cascade="all, delete-orphan")
    def __repr__(self):
        return f'<Lesson {self.title}>'

class Exercise(db.Model):
    __tablename__ = 'exercises'
    id = db.Column(db.Integer, primary_key=True)
    question = db.Column(db.Text, nullable=False)
    correct_answer = db.Column(db.String(255), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.id'), nullable=False)
    submissions = db.relationship('Submission', backref='exercise', lazy='dynamic', cascade="all, delete-orphan")
    def __repr__(self):
        return f'<Exercise {self.id}>'
        
class Submission(db.Model):
    __tablename__ = 'submissions'
    id = db.Column(db.Integer, primary_key=True)
    student_answer = db.Column(db.Text, nullable=False)
    is_correct = db.Column(db.Boolean, nullable=False)
    submitted_at = db.Column(db.DateTime, index=True, default=lambda: datetime.now(UTC))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False)

    def __repr__(self):
        return f'<Submission {self.id} by User {self.user_id}>'

# --- [THE IMMORTAL MEMORY - AKASHIC RECORDS] ---

class Conversation(db.Model):
    __tablename__ = 'conversations'
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=lambda: datetime.now(UTC), index=True)
    messages = db.relationship('Message', backref='conversation', lazy='dynamic', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Conversation {self.id} by User {self.user_id}>'

class Message(db.Model):
    __tablename__ = 'messages'
    id = db.Column(db.Integer, primary_key=True)
    conversation_id = db.Column(db.String(36), db.ForeignKey('conversations.id'), nullable=False)
    role = db.Column(db.String(50), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=lambda: datetime.now(UTC), index=True)
    tool_name = db.Column(db.String(100), nullable=True)
    
    # --- [THE WISDOM ENGINE - PHASE 3 UPGRADE] ---
    # This column will store the architect's feedback ('good', 'bad').
    # It's the mechanism by which the AI learns from its mistakes and successes.
    # We add an index to make searching for 'good' examples extremely fast.
    rating = db.Column(db.String(50), nullable=True, index=True)
    # --- نهاية الترقية ---

    def __repr__(self):
        return f'<Message {self.id} Role={self.role} Rating={self.rating}>'