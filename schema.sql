DROP TABLE IF EXISTS submissions;
DROP TABLE IF EXISTS exercises;
DROP TABLE IF EXISTS lessons;
DROP TABLE IF EXISTS subjects;
DROP TABLE IF EXISTS users;

CREATE TABLE users ( id SERIAL PRIMARY KEY, full_name VARCHAR(100) NOT NULL, email VARCHAR(100) UNIQUE NOT NULL, password_hash VARCHAR(200) NOT NULL, created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP );
CREATE TABLE subjects ( id SERIAL PRIMARY KEY, name VARCHAR(100) UNIQUE NOT NULL );
CREATE TABLE lessons ( id SERIAL PRIMARY KEY, title VARCHAR(200) NOT NULL, content TEXT NOT NULL, subject_id INTEGER NOT NULL, FOREIGN KEY (subject_id) REFERENCES subjects (id) );
CREATE TABLE exercises ( id SERIAL PRIMARY KEY, title VARCHAR(200) NOT NULL, content TEXT NOT NULL, correct_answer VARCHAR(200) NOT NULL, lesson_id INTEGER, FOREIGN KEY (lesson_id) REFERENCES lessons (id) );
CREATE TABLE submissions ( id SERIAL PRIMARY KEY, student_answer VARCHAR(200) NOT NULL, is_correct BOOLEAN NOT NULL, timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP, user_id INTEGER NOT NULL, exercise_id INTEGER NOT NULL, FOREIGN KEY (user_id) REFERENCES users (id), FOREIGN KEY (exercise_id) REFERENCES exercises (id) );

INSERT INTO subjects (name) VALUES ('الرياضيات'), ('الفيزياء'), ('معلومات عامة');
INSERT INTO lessons (title, content, subject_id) VALUES ('مقدمة في الجبر', 'هذا الدرس يغطي أساسيات الجبر...', 1), ('قوانين نيوتن', 'هذا الدرس يشرح قوانين نيوتن الثلاثة للحركة...', 2);
INSERT INTO exercises (title, content, correct_answer, lesson_id) VALUES ('عملية حسابية', 'ما هو ناتج 5 * 5 ؟', '25', 1), ('عاصمة فرنسا', 'ما هي عاصمة فرنسا؟', 'باريس', NULL);