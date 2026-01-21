import sqlite3
import hashlib

DB_NAME = "academic.db"

class Database:
    """Centralized database management"""

    @staticmethod
    def get_connection():
        return sqlite3.connect(DB_NAME)

    @staticmethod
    def execute(query: str, params=(), fetch=False):
        with Database.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            conn.commit()
            return cur.fetchall() if fetch else None

    @staticmethod
    def init_db():
        conn = Database.get_connection()
        cur = conn.cursor()

        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'teacher', 'student')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE,
            major TEXT,
            enrollment_year INTEGER,
            gpa REAL DEFAULT 0.0,
            status TEXT DEFAULT 'active' CHECK(status IN ('active', 'inactive', 'graduated'))
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            semester TEXT NOT NULL,
            credits INTEGER DEFAULT 3 CHECK(credits BETWEEN 1 AND 6),
            instructor TEXT,
            max_capacity INTEGER DEFAULT 30
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS grades (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            student_id TEXT NOT NULL,
            course_id TEXT NOT NULL,
            grade REAL CHECK(grade BETWEEN 0 AND 100),
            letter_grade TEXT,
            graded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(student_id) REFERENCES students(id) ON DELETE CASCADE,
            FOREIGN KEY(course_id) REFERENCES courses(id) ON DELETE CASCADE,
            UNIQUE(student_id, course_id)
        )""")

        cur.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )""")

        # default admin
        try:
            cur.execute(
                "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                ("admin", hashlib.sha256("admin123".encode()).hexdigest(), "admin"),
            )
        except sqlite3.IntegrityError:
            pass

        conn.commit()
        conn.close()
Database.init_db()
