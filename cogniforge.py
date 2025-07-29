# cogniforge.py - Final Corrected Version

from app import create_app, db
from app.models import User, Subject, Lesson, Exercise, Submission
import click

# --- 1. إنشاء كائن التطبيق أولاً ---
# هذا هو أهم تغيير. يجب أن ننشئ 'app' قبل استخدامه.
app = create_app()

# --- 2. الآن يمكننا استخدام 'app' لتعريف الأوامر ---

@app.shell_context_processor
def make_shell_context():
    """
    يجعل هذه الكائنات متاحة تلقائيًا في جلسة `flask shell`
    وهو أمر مفيد جدًا للتجربة والاختبار.
    """
    return {
        'db': db, 
        'User': User, 
        'Subject': Subject, 
        'Lesson': Lesson, 
        'Exercise': Exercise, 
        'Submission': Submission
    }

@app.cli.command("seed-db")
def seed_db():
    """Adds initial seed data to the database."""
    print("Seeding database with initial data...")
    
    # --- إضافة المواد ---
    subjects_to_add = ['الرياضيات', 'الفيزياء', 'معلومات عامة']
    for s_name in subjects_to_add:
        if not Subject.query.filter_by(name=s_name).first():
            subject = Subject(name=s_name)
            db.session.add(subject)
            print(f"Added subject: {s_name}")
    db.session.commit()

    # --- إضافة الدروس ---
    math_subject = Subject.query.filter_by(name='الرياضيات').first()
    physics_subject = Subject.query.filter_by(name='الفيزياء').first()
    general_subject = Subject.query.filter_by(name='معلومات عامة').first()

    if math_subject and not Lesson.query.filter_by(title='مقدمة في الجبر').first():
        lesson1 = Lesson(title='مقدمة في الجبر', content='هذا الدرس يغطي أساسيات الجبر...', subject=math_subject)
        db.session.add(lesson1)
        print("Added lesson: مقدمة في الجبر")

    if physics_subject and not Lesson.query.filter_by(title='قوانين نيوتن').first():
        lesson2 = Lesson(title='قوانين نيوتن', content='هذا الدرس يشرح قوانين نيوتن الثلاثة للحركة...', subject=physics_subject)
        db.session.add(lesson2)
        print("Added lesson: قوانين نيوتن")
    
    if general_subject and not Lesson.query.filter_by(title='عواصم ودول').first():
        capitals_lesson = Lesson(title='عواصم ودول', content='درس حول عواصم الدول.', subject=general_subject)
        db.session.add(capitals_lesson)
        print("Added lesson: عواصم ودول")
    
    db.session.commit()

    # --- إضافة التمارين ---
    algebra_lesson_db = Lesson.query.filter_by(title='مقدمة في الجبر').first()
    capitals_lesson_db = Lesson.query.filter_by(title='عواصم ودول').first()

    if algebra_lesson_db and not Exercise.query.filter_by(question='ما هو ناتج 5 * 5 ؟').first():
        ex1 = Exercise(question='ما هو ناتج 5 * 5 ؟', correct_answer='25', lesson=algebra_lesson_db)
        db.session.add(ex1)
        print("Added exercise: 5 * 5")

    if capitals_lesson_db and not Exercise.query.filter_by(question='ما هي عاصمة فرنسا؟').first():
        ex2 = Exercise(question='ما هي عاصمة فرنسا؟', correct_answer='باريس', lesson=capitals_lesson_db)
        db.session.add(ex2)
        print("Added exercise: عاصمة فرنسا")

    db.session.commit()
    print("Database seeding complete!")