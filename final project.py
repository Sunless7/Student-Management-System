import sqlite3
import tkinter as tk
from tkinter import messagebox, filedialog, ttk
import csv
import json
from datetime import datetime
import hashlib
import re
from typing import Optional, List, Tuple

# ============================================================
# DATABASE & CORE SETUP
# ============================================================

DB_NAME = "academic.db"

class Database:
    """Centralized database management with connection pooling"""
    
    @staticmethod
    def get_connection():
        return sqlite3.connect(DB_NAME)
    
    @staticmethod
    def execute(query: str, params=(), fetch=False):
        """Execute query with automatic connection management"""
        with Database.get_connection() as conn:
            cur = conn.cursor()
            cur.execute(query, params)
            conn.commit()  # FIX: Added commit for write operations
            return cur.fetchall() if fetch else None
    
    @staticmethod
    def init_db():
        """Initialize database schema with all required tables"""
        conn = Database.get_connection()
        cur = conn.cursor()
        
        # Users table with role-based access
        cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('admin', 'teacher', 'student')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )""")
        
        # Students table
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
        
        # Courses table
        cur.execute("""
        CREATE TABLE IF NOT EXISTS courses (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            semester TEXT NOT NULL,
            credits INTEGER DEFAULT 3 CHECK(credits BETWEEN 1 AND 6),
            instructor TEXT,
            max_capacity INTEGER DEFAULT 30
        )""")
        
        # Grades table with foreign key constraints
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
        
        # Activity log for audit trail
        cur.execute("""
        CREATE TABLE IF NOT EXISTS activity_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            action TEXT NOT NULL,
            details TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )""")
        
        # Create default admin user
        try:
            cur.execute("INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
                       ('admin', hashlib.sha256('admin123'.encode()).hexdigest(), 'admin'))
        except sqlite3.IntegrityError:
            pass  # Admin already exists
        
        conn.commit()
        conn.close()

# ============================================================
# BUSINESS LOGIC LAYER
# ============================================================

class StudentManager:
    """Handle all student-related operations"""
    
    @staticmethod
    def validate_email(email: str) -> bool:
        return bool(re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email))
    
    @staticmethod
    def add(sid: str, name: str, email: str, major: str, year: int, user_id: int):
        if len(sid) < 3 or not sid.isalnum():
            raise ValueError("Student ID must be at least 3 alphanumeric characters")
        if not name.strip():
            raise ValueError("Student name is required")
        if email and not StudentManager.validate_email(email):
            raise ValueError("Invalid email format")
        
        Database.execute(
            "INSERT INTO students (id, name, email, major, enrollment_year) VALUES (?, ?, ?, ?, ?)",
            (sid, name, email or None, major, year)
        )
        ActivityLog.log(user_id, "add_student", f"Added: {name} ({sid})")
    
    @staticmethod
    def update(sid: str, name: str, email: str, major: str, status: str, user_id: int):
        if email and not StudentManager.validate_email(email):
            raise ValueError("Invalid email format")
        
        Database.execute(
            "UPDATE students SET name=?, email=?, major=?, status=? WHERE id=?",
            (name, email or None, major, status, sid)
        )
        ActivityLog.log(user_id, "update_student", f"Updated: {sid}")
    
    @staticmethod
    def delete(sid: str, user_id: int):
        """Delete a student and all associated grades"""
        # Get student name before deletion for logging
        result = Database.execute(
            "SELECT name FROM students WHERE id = ?", (sid,), fetch=True
        )
        if not result:
            raise ValueError(f"Student {sid} not found")
        
        student_name = result[0][0]
        Database.execute("DELETE FROM students WHERE id = ?", (sid,))
        ActivityLog.log(user_id, "delete_student", f"Deleted: {student_name} ({sid})")
        return student_name
    
    @staticmethod
    def delete_all(user_id: int):
        """Delete all students and their grades"""
        count = Database.execute("SELECT COUNT(*) FROM students", fetch=True)[0][0]
        Database.execute("DELETE FROM students")
        ActivityLog.log(user_id, "delete_all_students", f"Deleted all {count} students")
        return count
    
    @staticmethod
    def search(query: str) -> List[Tuple]:
        pattern = f"%{query}%"
        return Database.execute(
            "SELECT * FROM students WHERE id LIKE ? OR name LIKE ? OR major LIKE ?",
            (pattern, pattern, pattern), fetch=True
        )
    
    @staticmethod
    def get_all() -> List[Tuple]:
        return Database.execute("SELECT * FROM students ORDER BY name", fetch=True)
    
    @staticmethod
    def get_transcript(sid: str) -> List[Tuple]:
        return Database.execute("""
            SELECT c.name, c.semester, c.credits, g.grade, g.letter_grade, g.graded_at
            FROM grades g
            JOIN courses c ON c.id = g.course_id
            WHERE g.student_id = ?
            ORDER BY c.semester DESC, c.name
        """, (sid,), fetch=True)

class CourseManager:
    """Handle all course-related operations"""
    
    @staticmethod
    def add(cid: str, name: str, semester: str, credits: int, instructor: str, user_id: int):
        if not all([cid, name, semester]):
            raise ValueError("Course ID, name, and semester are required")
        if not (1 <= credits <= 6):
            raise ValueError("Credits must be between 1 and 6")
        
        Database.execute(
            "INSERT INTO courses (id, name, semester, credits, instructor) VALUES (?, ?, ?, ?, ?)",
            (cid, name, semester, credits, instructor)
        )
        ActivityLog.log(user_id, "add_course", f"Added: {name} ({cid})")
    
    @staticmethod
    def delete(cid: str, user_id: int):
        """Delete a course and all associated grades"""
        # Get course name before deletion for logging
        result = Database.execute(
            "SELECT name FROM courses WHERE id = ?", (cid,), fetch=True
        )
        if not result:
            raise ValueError(f"Course {cid} not found")
        
        course_name = result[0][0]
        Database.execute("DELETE FROM courses WHERE id = ?", (cid,))
        ActivityLog.log(user_id, "delete_course", f"Deleted: {course_name} ({cid})")
        return course_name
    
    @staticmethod
    def delete_all(user_id: int):
        """Delete all courses and their grades"""
        count = Database.execute("SELECT COUNT(*) FROM courses", fetch=True)[0][0]
        Database.execute("DELETE FROM courses")
        ActivityLog.log(user_id, "delete_all_courses", f"Deleted all {count} courses")
        return count
    
    @staticmethod
    def get_all() -> List[Tuple]:
        return Database.execute("SELECT * FROM courses ORDER BY semester, name", fetch=True)
    
    @staticmethod
    def get_enrollment(course_id: str) -> int:
        result = Database.execute(
            "SELECT COUNT(*) FROM grades WHERE course_id = ?",
            (course_id,), fetch=True
        )
        return result[0][0] if result else 0

class GradeManager:
    """Handle all grade-related operations"""
    
    @staticmethod
    def calculate_letter(grade: float) -> str:
        if grade >= 90: return 'A'
        elif grade >= 80: return 'B'
        elif grade >= 70: return 'C'
        elif grade >= 60: return 'D'
        else: return 'F'
    
    @staticmethod
    def grade_to_gpa_points(grade: float) -> float:
        """Convert numerical grade (0-100) to GPA points (0-4.0)"""
        if grade >= 90: return 4.0
        elif grade >= 80: return 3.0
        elif grade >= 70: return 2.0
        elif grade >= 60: return 1.0
        else: return 0.0
    
    @staticmethod
    def add(sid: str, cid: str, grade: float, user_id: int):
        try:
            grade = float(grade)
            if not (0 <= grade <= 100):
                raise ValueError("Grade must be between 0 and 100")
        except (ValueError, TypeError):
            raise ValueError("Invalid grade value")
        
        letter = GradeManager.calculate_letter(grade)
        Database.execute(
            "INSERT OR REPLACE INTO grades (student_id, course_id, grade, letter_grade) VALUES (?, ?, ?, ?)",
            (sid, cid, grade, letter)
        )
        
        # Update student GPA
        GradeManager.update_student_gpa(sid)
        ActivityLog.log(user_id, "add_grade", f"Grade {grade} for {sid} in {cid}")
    
    @staticmethod
    def update_student_gpa(sid: str):
        """Recalculate and update student's weighted GPA on 4.0 scale"""
        # Get all grades with credits for this student
        result = Database.execute("""
            SELECT g.grade, c.credits
            FROM grades g
            JOIN courses c ON c.id = g.course_id
            WHERE g.student_id = ?
        """, (sid,), fetch=True)
        
        if result:
            total_points = 0
            total_credits = 0
            
            for grade, credits in result:
                gpa_points = GradeManager.grade_to_gpa_points(grade)
                total_points += gpa_points * credits
                total_credits += credits
            
            if total_credits > 0:
                gpa = total_points / total_credits
                Database.execute("UPDATE students SET gpa = ? WHERE id = ?", 
                               (round(gpa, 2), sid))
    
    @staticmethod
    def get_failing_students() -> List[Tuple]:
        return Database.execute("""
            SELECT s.name, s.id, s.email, c.name, g.grade, g.letter_grade
            FROM grades g
            JOIN students s ON s.id = g.student_id
            JOIN courses c ON c.id = g.course_id
            WHERE g.grade < 60
            ORDER BY s.name, c.name
        """, fetch=True)

class Analytics:
    """Advanced analytics and reporting"""
    
    @staticmethod
    def get_gpa_rankings() -> List[Tuple]:
        return Database.execute("""
            SELECT name, id, gpa, 
                   (SELECT COUNT(*) FROM grades WHERE student_id = students.id) as courses
            FROM students
            WHERE gpa > 0
            ORDER BY gpa DESC
        """, fetch=True)
    
    @staticmethod
    def get_academic_status() -> List[Tuple]:
        """Classify students by academic standing"""
        results = []
        rankings = Analytics.get_gpa_rankings()
        if rankings:  # FIX: Check if results exist
            for name, sid, gpa, courses in rankings:
                if gpa >= 3.5:
                    status = "Dean's List"
                elif gpa >= 2.0:
                    status = "Good Standing"
                elif gpa >= 1.0:
                    status = "Warning"
                else:
                    status = "Academic Probation"
                results.append((name, sid, gpa, courses, status))
        return results
    
    @staticmethod
    def get_course_statistics() -> List[Tuple]:
        return Database.execute("""
            SELECT c.name, c.semester, COUNT(DISTINCT g.student_id) as enrolled,
                   ROUND(AVG(g.grade), 2) as avg_grade,
                   MIN(g.grade) as min_grade,
                   MAX(g.grade) as max_grade
            FROM grades g
            JOIN courses c ON c.id = g.course_id
            GROUP BY c.id
            ORDER BY avg_grade DESC
        """, fetch=True)

class ActivityLog:
    """Centralized activity logging"""
    
    @staticmethod
    def log(user_id: int, action: str, details: str = ""):
        Database.execute(
            "INSERT INTO activity_log (user_id, action, details) VALUES (?, ?, ?)",
            (user_id, action, details)
        )

class ImportExport:
    """Handle data import/export operations"""
    
    @staticmethod
    def import_students_csv(path: str, user_id: int) -> int:
        count = 0
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    Database.execute(
                        "INSERT OR IGNORE INTO students (id, name, email, major, enrollment_year) VALUES (?, ?, ?, ?, ?)",
                        (row.get('id'), row.get('name'), row.get('email'), 
                         row.get('major'), int(row.get('enrollment_year', 2024)))
                    )
                    count += 1
                except Exception as e:
                    print(f"Skipped row: {e}")
        
        ActivityLog.log(user_id, "import_students", f"Imported {count} students")
        return count
    
    @staticmethod
    def export_full_report(path: str, user_id: int):
        rows = Database.execute("""
            SELECT s.id, s.name, s.email, s.major, s.gpa,
                   c.id, c.name, c.semester, g.grade, g.letter_grade
            FROM grades g
            JOIN students s ON s.id = g.student_id
            JOIN courses c ON c.id = g.course_id
            ORDER BY s.name, c.semester
        """, fetch=True)
        
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Student_ID", "Name", "Email", "Major", "GPA",
                           "Course_ID", "Course", "Semester", "Grade", "Letter"])
            writer.writerows(rows)
        
        ActivityLog.log(user_id, "export_report", f"Exported to {path}")

class Auth:
    """Authentication system"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        return hashlib.sha256(password.encode()).hexdigest()
    
    @staticmethod
    def authenticate(username: str, password: str) -> Optional[Tuple]:
        rows = Database.execute(
            "SELECT id, username, role FROM users WHERE username = ? AND password_hash = ?",
            (username, Auth.hash_password(password)), fetch=True
        )
        return rows[0] if rows else None

# ============================================================
# USER INTERFACE
# ============================================================

class LoginWindow:
    """Login interface"""
    
    def __init__(self, root):
        self.root = root
        self.root.title("Academic System - Login")
        self.root.geometry("400x250")
        self.root.resizable(False, False)
        self.center_window()
        
        self.user_data = None
        self.setup_ui()
    
    def center_window(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - 200
        y = (self.root.winfo_screenheight() // 2) - 125
        self.root.geometry(f"400x250+{x}+{y}")
    
    def setup_ui(self):
        frame = tk.Frame(self.root, padx=40, pady=40)
        frame.pack(expand=True)
        
        tk.Label(frame, text="Academic Performance System", 
                font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        tk.Label(frame, text="Username:").grid(row=1, column=0, sticky="e", pady=5)
        self.username_entry = tk.Entry(frame, width=25)
        self.username_entry.grid(row=1, column=1, pady=5)
        
        tk.Label(frame, text="Password:").grid(row=2, column=0, sticky="e", pady=5)
        self.password_entry = tk.Entry(frame, width=25, show="*")
        self.password_entry.grid(row=2, column=1, pady=5)
        
        tk.Button(frame, text="Login", command=self.login, width=20,
                 bg="#4CAF50", fg="white").grid(row=3, column=0, columnspan=2, pady=(20, 5))
        
        tk.Label(frame, text="Default: admin / admin123", 
                font=("Arial", 8), fg="gray").grid(row=4, column=0, columnspan=2)
        
        # Bind Enter key
        self.password_entry.bind("<Return>", lambda e: self.login())
        self.username_entry.focus()
    
    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()
        
        if not username or not password:
            messagebox.showerror("Error", "Please enter credentials")
            return
        
        user_data = Auth.authenticate(username, password)
        
        if user_data:
            self.user_data = user_data
            ActivityLog.log(user_data[0], "login", f"User logged in: {username}")
            self.root.destroy()
        else:
            messagebox.showerror("Error", "Invalid credentials")
            self.password_entry.delete(0, tk.END)

class AcademicApp:
    """Main application interface"""
    
    def __init__(self, root, user_data):
        self.root = root
        self.user_id, self.username, self.role = user_data
        
        self.root.title(f"Academic System - {self.username} ({self.role})")
        self.root.geometry("1200x700")
        
        self.setup_ui()
        self.load_data()
    
    def setup_ui(self):
        # Create tabbed interface
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Initialize tabs
        self.setup_students_tab()
        self.setup_courses_tab()
        self.setup_grades_tab()
        self.setup_analytics_tab()
        
        # Status bar
        status = tk.Label(self.root, text=f"Logged in as {self.username}", 
                         relief=tk.SUNKEN, anchor="w", bg="#f0f0f0")
        status.pack(side=tk.BOTTOM, fill=tk.X)
    
    def setup_students_tab(self):
        tab = tk.Frame(self.notebook)
        self.notebook.add(tab, text="Students")
        
        # Left panel - forms
        left = tk.Frame(tab, padx=10, pady=10)
        left.pack(side=tk.LEFT, fill=tk.Y)
        
        tk.Label(left, text="Student Management", 
                font=("Arial", 12, "bold")).pack(pady=(0, 10))
        
        # Input fields
        self.student_entries = {}
        for label, key in [("ID*:", "id"), ("Name*:", "name"), ("Email:", "email"),
                          ("Major:", "major"), ("Year:", "year")]:
            tk.Label(left, text=label).pack(anchor="w")
            entry = tk.Entry(left, width=30)
            entry.pack(pady=(0, 5))
            self.student_entries[key] = entry
        
        tk.Label(left, text="Status:").pack(anchor="w")
        self.student_status = tk.StringVar(value="active")
        ttk.Combobox(left, textvariable=self.student_status,
                    values=["active", "inactive", "graduated"],
                    state="readonly", width=28).pack(pady=(0, 10))
        
        # Buttons
        tk.Button(left, text="Add Student", command=self.add_student,
                 bg="#4CAF50", fg="white").pack(fill=tk.X, pady=2)
        tk.Button(left, text="Update Selected", command=self.update_student,
                 bg="#2196F3", fg="white").pack(fill=tk.X, pady=2)
        tk.Button(left, text="Delete Selected", command=self.delete_student,
                 bg="#F44336", fg="white").pack(fill=tk.X, pady=2)
        tk.Button(left, text="Delete All Students", command=self.delete_all_students,
                 bg="#B71C1C", fg="white").pack(fill=tk.X, pady=2)
        tk.Button(left, text="View Transcript", command=self.view_transcript,
                 bg="#FF9800", fg="white").pack(fill=tk.X, pady=2)
        tk.Button(left, text="Clear Fields", command=self.clear_student_fields,
                 bg="#607D8B", fg="white").pack(fill=tk.X, pady=2)
        tk.Button(left, text="Import CSV", command=self.import_students,
                 bg="#9C27B0", fg="white").pack(fill=tk.X, pady=(15, 2))
        
        # Right panel - list
        right = tk.Frame(tab)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Search
        search_frame = tk.Frame(right)
        search_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.student_search = tk.StringVar()
        tk.Entry(search_frame, textvariable=self.student_search, width=30).pack(side=tk.LEFT, padx=5)
        tk.Button(search_frame, text="Search", command=self.search_students).pack(side=tk.LEFT)
        tk.Button(search_frame, text="Show All", command=self.load_students).pack(side=tk.LEFT, padx=5)
        
        # Treeview
        self.students_tree = ttk.Treeview(right,
            columns=("ID", "Name", "Email", "Major", "Year", "GPA", "Status"),
            show="headings", height=25)
        
        for col in self.students_tree["columns"]:
            self.students_tree.heading(col, text=col)
            self.students_tree.column(col, width=100 if col != "Name" else 150)
        
        scrollbar = ttk.Scrollbar(right, orient=tk.VERTICAL, command=self.students_tree.yview)
        self.students_tree.configure(yscrollcommand=scrollbar.set)
        
        self.students_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.students_tree.bind("<<TreeviewSelect>>", self.on_student_select)
    
    def setup_courses_tab(self):
        tab = tk.Frame(self.notebook)
        self.notebook.add(tab, text="Courses")
        
        # Left panel - forms
        left = tk.Frame(tab, padx=10, pady=10)
        left.pack(side=tk.LEFT, fill=tk.Y)
        
        tk.Label(left, text="Course Management", 
                font=("Arial", 12, "bold")).pack(pady=(0, 10))
        
        # Input fields
        self.course_entries = {}
        for label, key in [("Course ID*:", "id"), ("Course Name*:", "name"), 
                          ("Semester*:", "semester"), ("Credits (1-6)*:", "credits"),
                          ("Instructor:", "instructor")]:
            tk.Label(left, text=label).pack(anchor="w")
            entry = tk.Entry(left, width=30)
            entry.pack(pady=(0, 5))
            self.course_entries[key] = entry
        
        # Buttons
        tk.Button(left, text="Add Course", command=self.add_course,
                 bg="#4CAF50", fg="white").pack(fill=tk.X, pady=2)
        tk.Button(left, text="Delete Selected", command=self.delete_course,
                 bg="#F44336", fg="white").pack(fill=tk.X, pady=2)
        tk.Button(left, text="Delete All Courses", command=self.delete_all_courses,
                 bg="#B71C1C", fg="white").pack(fill=tk.X, pady=2)
        tk.Button(left, text="Clear Fields", command=self.clear_course_fields,
                 bg="#607D8B", fg="white").pack(fill=tk.X, pady=2)
        
        # Right panel - list
        right = tk.Frame(tab)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(right, text="Available Courses", 
                font=("Arial", 11, "bold")).pack(pady=(0, 5))
        
        # Treeview
        self.courses_tree = ttk.Treeview(right,
            columns=("ID", "Name", "Semester", "Credits", "Instructor", "Capacity"),
            show="headings", height=25)
        
        for col in self.courses_tree["columns"]:
            self.courses_tree.heading(col, text=col)
            width = 200 if col == "Name" else 100
            self.courses_tree.column(col, width=width)
        
        scrollbar = ttk.Scrollbar(right, orient=tk.VERTICAL, command=self.courses_tree.yview)
        self.courses_tree.configure(yscrollcommand=scrollbar.set)
        
        self.courses_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.courses_tree.bind("<<TreeviewSelect>>", self.on_course_select)
    
    def setup_grades_tab(self):
        tab = tk.Frame(self.notebook)
        self.notebook.add(tab, text="Grades & Failing Students")
        
        # Left panel
        left = tk.Frame(tab, padx=10, pady=10)
        left.pack(side=tk.LEFT, fill=tk.Y)
        
        tk.Label(left, text="Grade Entry", font=("Arial", 12, "bold")).pack(pady=(0, 10))
        
        tk.Label(left, text="Student ID:").pack(anchor="w")
        self.grade_student = tk.Entry(left, width=30)
        self.grade_student.pack(pady=(0, 5))
        
        tk.Label(left, text="Course ID:").pack(anchor="w")
        self.grade_course = tk.Entry(left, width=30)
        self.grade_course.pack(pady=(0, 5))
        
        tk.Label(left, text="Grade (0-100):").pack(anchor="w")
        self.grade_value = tk.Entry(left, width=30)
        self.grade_value.pack(pady=(0, 10))
        
        tk.Button(left, text="Record Grade", command=self.add_grade,
                 bg="#4CAF50", fg="white").pack(fill=tk.X)
        
        # Right panel - failing students
        right = tk.Frame(tab)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tk.Label(right, text="Failing Students (Grade < 60)",
                font=("Arial", 11, "bold")).pack(pady=(0, 5))
        
        self.failing_tree = ttk.Treeview(right,
            columns=("Student", "ID", "Email", "Course", "Grade", "Letter"),
            show="headings", height=25)
        
        for col in self.failing_tree["columns"]:
            self.failing_tree.heading(col, text=col)
            self.failing_tree.column(col, width=120 if col == "Student" else 100)
        
        scrollbar = ttk.Scrollbar(right, orient=tk.VERTICAL, command=self.failing_tree.yview)
        self.failing_tree.configure(yscrollcommand=scrollbar.set)
        
        self.failing_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    def setup_analytics_tab(self):
        tab = tk.Frame(self.notebook)
        self.notebook.add(tab, text="Analytics & Reports")
        
        btn_frame = tk.Frame(tab, padx=10, pady=10)
        btn_frame.pack(side=tk.TOP, fill=tk.X)
        
        tk.Button(btn_frame, text="Show GPA Rankings", 
                 command=self.show_gpa_rankings, bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Academic Status Report",
                 command=self.show_academic_status, bg="#FF9800", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Course Statistics",
                 command=self.show_course_stats, bg="#9C27B0", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Export Full Report",
                 command=self.export_report, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)
        
        # Results area
        self.analytics_tree = ttk.Treeview(tab, show="headings", height=30)
        scrollbar = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=self.analytics_tree.yview)
        self.analytics_tree.configure(yscrollcommand=scrollbar.set)
        
        self.analytics_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
    
    # Event handlers
    def load_data(self):
        self.load_students()
        self.load_courses()
        self.load_failing_students()
    
    def load_students(self):
        self.students_tree.delete(*self.students_tree.get_children())
        results = StudentManager.get_all()
        if results:  # FIX: Check if results exist
            for row in results:
                # Convert row to list and ensure ID is string to preserve leading zeros
                row_list = list(row)
                row_list[0] = str(row_list[0])  # Ensure ID is string
                self.students_tree.insert("", tk.END, values=row_list)
    
    def load_courses(self):
        self.courses_tree.delete(*self.courses_tree.get_children())
        results = CourseManager.get_all()
        if results:
            for row in results:
                self.courses_tree.insert("", tk.END, values=row)
    
    def load_failing_students(self):
        self.failing_tree.delete(*self.failing_tree.get_children())
        results = GradeManager.get_failing_students()
        if results:  # FIX: Check if results exist
            for row in results:
                self.failing_tree.insert("", tk.END, values=row)
    
    def search_students(self):
        query = self.student_search.get()
        if not query:
            self.load_students()
            return
        
        self.students_tree.delete(*self.students_tree.get_children())
        results = StudentManager.search(query)
        if results:  # FIX: Check if results exist
            for row in results:
                # Convert row to list and ensure ID is string to preserve leading zeros
                row_list = list(row)
                row_list[0] = str(row_list[0])  # Ensure ID is string
                self.students_tree.insert("", tk.END, values=row_list)
    
    def add_student(self):
        try:
            StudentManager.add(
                self.student_entries["id"].get(),
                self.student_entries["name"].get(),
                self.student_entries["email"].get(),
                self.student_entries["major"].get(),
                int(self.student_entries["year"].get() or 2024),
                self.user_id
            )
            messagebox.showinfo("Success", "Student added successfully")
            self.load_students()
            self.clear_student_fields()
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def update_student(self):
        selected = self.students_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a student")
            return
        
        try:
            StudentManager.update(
                self.student_entries["id"].get(),
                self.student_entries["name"].get(),
                self.student_entries["email"].get(),
                self.student_entries["major"].get(),
                self.student_status.get(),
                self.user_id
            )
            messagebox.showinfo("Success", "Student updated")
            self.load_students()
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def delete_student(self):
        selected = self.students_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a student to delete")
            return
        
        # Get student info from selection
        values = self.students_tree.item(selected[0])['values']
        student_id = values[0]
        student_name = values[1]
        
        # Confirmation dialog
        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete student:\n\n"
            f"ID: {student_id}\n"
            f"Name: {student_name}\n\n"
            f"This will also delete all their grades!\n"
            f"This action cannot be undone."
        )
        
        if confirm:
            try:
                deleted_name = StudentManager.delete(student_id, self.user_id)
                messagebox.showinfo("Success", f"Student '{deleted_name}' deleted successfully")
                self.load_students()
                self.load_failing_students()  # Refresh in case they were failing
                self.clear_student_fields()
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    def delete_all_students(self):
        """Delete all students from the database"""
        # Count current students
        student_count = len(self.students_tree.get_children())
        
        if student_count == 0:
            messagebox.showinfo("Info", "There are no students to delete")
            return
        
        # Strong confirmation dialog
        confirm = messagebox.askyesno(
            "⚠️ WARNING: Delete All Students ⚠️",
            f"You are about to DELETE ALL {student_count} STUDENTS!\n\n"
            f"This will also delete:\n"
            f"• All student records\n"
            f"• All grades for all students\n"
            f"• All academic history\n\n"
            f"THIS CANNOT BE UNDONE!\n\n"
            f"Are you absolutely sure you want to continue?",
            icon='warning'
        )
        
        if not confirm:
            return
        
        # Second confirmation
        double_confirm = messagebox.askyesno(
            "Final Confirmation",
            f"This is your FINAL warning!\n\n"
            f"Deleting {student_count} students and all their data.\n\n"
            f"Type YES to confirm deletion:",
            icon='warning'
        )
        
        if double_confirm:
            try:
                count = StudentManager.delete_all(self.user_id)
                messagebox.showinfo("Complete", f"Successfully deleted all {count} students and their grades")
                self.load_students()
                self.load_failing_students()
                self.clear_student_fields()
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    def on_student_select(self, event):
        selected = self.students_tree.selection()
        if selected:
            values = self.students_tree.item(selected[0])['values']
            # Clear all fields first
            for entry in self.student_entries.values():
                entry.delete(0, tk.END)
            
            # Fill fields with proper data - convert to string to preserve leading zeros
            self.student_entries["id"].insert(0, str(values[0]))
            self.student_entries["name"].insert(0, str(values[1]))
            self.student_entries["email"].insert(0, str(values[2]) if values[2] else "")
            self.student_entries["major"].insert(0, str(values[3]) if values[3] else "")
            self.student_entries["year"].insert(0, str(values[4]) if values[4] else "")
            self.student_status.set(values[6])
    
    def clear_student_fields(self):
        for entry in self.student_entries.values():
            entry.delete(0, tk.END)
    
    def add_course(self):
        try:
            CourseManager.add(
                self.course_entries["id"].get(),
                self.course_entries["name"].get(),
                self.course_entries["semester"].get(),
                int(self.course_entries["credits"].get() or 3),
                self.course_entries["instructor"].get(),
                self.user_id
            )
            messagebox.showinfo("Success", "Course added successfully")
            self.load_courses()
            self.clear_course_fields()
        except Exception as e:
            messagebox.showerror("Error", str(e))
    
    def on_course_select(self, event):
        selected = self.courses_tree.selection()
        if selected:
            values = self.courses_tree.item(selected[0])['values']
            self.course_entries["id"].delete(0, tk.END)
            self.course_entries["id"].insert(0, values[0])
            self.course_entries["name"].delete(0, tk.END)
            self.course_entries["name"].insert(0, values[1])
            self.course_entries["semester"].delete(0, tk.END)
            self.course_entries["semester"].insert(0, values[2])
            self.course_entries["credits"].delete(0, tk.END)
            self.course_entries["credits"].insert(0, values[3])
            self.course_entries["instructor"].delete(0, tk.END)
            self.course_entries["instructor"].insert(0, values[4] or "")
    
    def clear_course_fields(self):
        for entry in self.course_entries.values():
            entry.delete(0, tk.END)
    
    def delete_course(self):
        selected = self.courses_tree.selection()
        if not selected:
            messagebox.showwarning("Warning", "Please select a course to delete")
            return
        
        # Get course info from selection
        values = self.courses_tree.item(selected[0])['values']
        course_id = values[0]
        course_name = values[1]
        
        # Confirmation dialog
        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete course:\n\n"
            f"ID: {course_id}\n"
            f"Name: {course_name}\n\n"
            f"This will also delete all grades for this course!\n"
            f"This action cannot be undone."
        )
        
        if confirm:
            try:
                deleted_name = CourseManager.delete(course_id, self.user_id)
                messagebox.showinfo("Success", f"Course '{deleted_name}' deleted successfully")
                self.load_courses()
                self.load_failing_students()  # Refresh in case it affects failing students
                self.load_students()  # Refresh to update GPAs
                self.clear_course_fields()
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    def delete_all_courses(self):
        """Delete all courses from the database"""
        # Count current courses
        course_count = len(self.courses_tree.get_children())
        
        if course_count == 0:
            messagebox.showinfo("Info", "There are no courses to delete")
            return
        
        # Strong confirmation dialog
        confirm = messagebox.askyesno(
            "⚠️ WARNING: Delete All Courses ⚠️",
            f"You are about to DELETE ALL {course_count} COURSES!\n\n"
            f"This will also delete:\n"
            f"• All course records\n"
            f"• All grades for all courses\n"
            f"• All student GPAs will be reset to 0.0\n\n"
            f"THIS CANNOT BE UNDONE!\n\n"
            f"Are you absolutely sure you want to continue?",
            icon='warning'
        )
        
        if not confirm:
            return
        
        # Second confirmation
        double_confirm = messagebox.askyesno(
            "Final Confirmation",
            f"This is your FINAL warning!\n\n"
            f"Deleting {course_count} courses and all grades.\n\n"
            f"Continue with deletion?",
            icon='warning'
        )
        
        if double_confirm:
            try:
                count = CourseManager.delete_all(self.user_id)
                # Reset all student GPAs to 0
                Database.execute("UPDATE students SET gpa = 0.0")
                messagebox.showinfo("Complete", f"Successfully deleted all {count} courses and their grades")
                self.load_courses()
                self.load_students()  # Refresh to show reset GPAs
                self.load_failing_students()
                self.clear_course_fields()
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    def view_transcript(self):
        sid = self.student_entries["id"].get()
        if not sid:
            messagebox.showwarning("Warning", "Please enter a student ID")
            return
        
        transcript = StudentManager.get_transcript(sid)
        if not transcript:
            messagebox.showinfo("Info", "No grades found for this student")
            return
        
        # Create popup window
        popup = tk.Toplevel(self.root)
        popup.title(f"Transcript - {sid}")
        popup.geometry("800x400")
        
        tree = ttk.Treeview(popup,
            columns=("Course", "Semester", "Credits", "Grade", "Letter", "Date"),
            show="headings", height=15)
        
        for col in tree["columns"]:
            tree.heading(col, text=col)
            tree.column(col, width=120)
        
        for row in transcript:
            tree.insert("", tk.END, values=row)
        
        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    def add_grade(self):
        try:
            student_id = self.grade_student.get().strip()
            course_id = self.grade_course.get().strip()
            grade_value = self.grade_value.get().strip()
            
            # Better validation
            if not student_id:
                messagebox.showerror("Error", "Please enter a Student ID")
                return
            if not course_id:
                messagebox.showerror("Error", "Please enter a Course ID")
                return
            if not grade_value:
                messagebox.showerror("Error", "Please enter a grade value")
                return
            
            # Check if student exists
            student_check = Database.execute(
                "SELECT id FROM students WHERE id = ?", (student_id,), fetch=True
            )
            if not student_check:
                messagebox.showerror("Error", f"Student ID '{student_id}' does not exist!\nPlease add the student first.")
                return
            
            # Check if course exists
            course_check = Database.execute(
                "SELECT id FROM courses WHERE id = ?", (course_id,), fetch=True
            )
            if not course_check:
                messagebox.showerror("Error", f"Course ID '{course_id}' does not exist!\nPlease add the course first in the Courses tab.")
                return
            
            GradeManager.add(student_id, course_id, float(grade_value), self.user_id)
            messagebox.showinfo("Success", f"Grade {grade_value} recorded for {student_id} in {course_id}")
            self.load_failing_students()
            self.load_students()  # Refresh to show updated GPA
            self.grade_student.delete(0, tk.END)
            self.grade_course.delete(0, tk.END)
            self.grade_value.delete(0, tk.END)
        except ValueError as ve:
            messagebox.showerror("Error", str(ve))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to record grade: {str(e)}")
    
    def import_students(self):
        path = filedialog.askopenfilename(
            title="Select CSV File", filetypes=[("CSV Files", "*.csv")]
        )
        if path:
            try:
                count = ImportExport.import_students_csv(path, self.user_id)
                messagebox.showinfo("Success", f"Imported {count} students")
                self.load_students()
            except Exception as e:
                messagebox.showerror("Error", str(e))
    
    def show_gpa_rankings(self):
        self.analytics_tree.delete(*self.analytics_tree.get_children())
        self.analytics_tree["columns"] = ("Name", "ID", "GPA", "Courses")
        
        for col in self.analytics_tree["columns"]:
            self.analytics_tree.heading(col, text=col)
            self.analytics_tree.column(col, width=150 if col == "Name" else 100)
        
        results = Analytics.get_gpa_rankings()
        if results:  # FIX: Check if results exist
            for row in results:
                self.analytics_tree.insert("", tk.END, values=row)
    
    def show_academic_status(self):
        self.analytics_tree.delete(*self.analytics_tree.get_children())
        self.analytics_tree["columns"] = ("Name", "ID", "GPA", "Courses", "Status")
        
        for col in self.analytics_tree["columns"]:
            self.analytics_tree.heading(col, text=col)
            self.analytics_tree.column(col, width=150 if col == "Name" else 100)
        
        results = Analytics.get_academic_status()
        if results:  # FIX: Check if results exist
            for row in results:
                self.analytics_tree.insert("", tk.END, values=row)
    
    def show_course_stats(self):
        self.analytics_tree.delete(*self.analytics_tree.get_children())
        self.analytics_tree["columns"] = ("Course", "Semester", "Enrolled", "Avg Grade", "Min Grade", "Max Grade")
        
        for col in self.analytics_tree["columns"]:
            self.analytics_tree.heading(col, text=col)
            self.analytics_tree.column(col, width=150 if col == "Course" else 100)
        
        results = Analytics.get_course_statistics()
        if results:  # FIX: Check if results exist
            for row in results:
                self.analytics_tree.insert("", tk.END, values=row)
    
    def export_report(self):
        path = filedialog.asksaveasfilename(
            title="Save Report As", defaultextension=".csv",
            filetypes=[("CSV Files", "*.csv")]
        )
        if path:
            try:
                ImportExport.export_full_report(path, self.user_id)
                messagebox.showinfo("Success", f"Report exported to {path}")
            except Exception as e:
                messagebox.showerror("Error", str(e))

# ============================================================
# MAIN PROGRAM
# ============================================================

if __name__ == "__main__":
    Database.init_db()
    
    root = tk.Tk()
    login_window = LoginWindow(root)
    root.mainloop()
    
    if login_window.user_data:
        app_root = tk.Tk()
        app = AcademicApp(app_root, login_window.user_data)
        app_root.mainloop()

# ============================================================
# END OF FILE
# ============================================================
