import re
import csv
from typing import Optional, List, Tuple
from database import Database

class ActivityLog:
    @staticmethod
    def log(user_id: int, action: str, details: str = ""):
        Database.execute(
            "INSERT INTO activity_log (user_id, action, details) VALUES (?, ?, ?)",
            (user_id, action, details),
        )

class StudentManager:
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
            (sid, name, email or None, major, year),
        )
        ActivityLog.log(user_id, "add_student", f"Added: {name} ({sid})")

    @staticmethod
    def update(sid: str, name: str, email: str, major: str, status: str, user_id: int):
        if email and not StudentManager.validate_email(email):
            raise ValueError("Invalid email format")

        Database.execute(
            "UPDATE students SET name=?, email=?, major=?, status=? WHERE id=?",
            (name, email or None, major, status, sid),
        )
        ActivityLog.log(user_id, "update_student", f"Updated: {sid}")

    @staticmethod
    def delete(sid: str, user_id: int):
        result = Database.execute("SELECT name FROM students WHERE id = ?", (sid,), fetch=True)
        if not result:
            raise ValueError(f"Student {sid} not found")
        student_name = result[0][0]

        Database.execute("DELETE FROM students WHERE id = ?", (sid,))
        ActivityLog.log(user_id, "delete_student", f"Deleted: {student_name} ({sid})")
        return student_name

    @staticmethod
    def delete_all(user_id: int):
        count = Database.execute("SELECT COUNT(*) FROM students", fetch=True)[0][0]
        Database.execute("DELETE FROM students")
        ActivityLog.log(user_id, "delete_all_students", f"Deleted all {count} students")
        return count

    @staticmethod
    def search(query: str) -> List[Tuple]:
        pattern = f"%{query}%"
        return Database.execute(
            "SELECT * FROM students WHERE id LIKE ? OR name LIKE ? OR major LIKE ?",
            (pattern, pattern, pattern),
            fetch=True,
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
    @staticmethod
    def add(cid: str, name: str, semester: str, credits: int, instructor: str, user_id: int):
        if not all([cid, name, semester]):
            raise ValueError("Course ID, name, and semester are required")
        if not (1 <= credits <= 6):
            raise ValueError("Credits must be between 1 and 6")

        Database.execute(
            "INSERT INTO courses (id, name, semester, credits, instructor) VALUES (?, ?, ?, ?, ?)",
            (cid, name, semester, credits, instructor),
        )
        ActivityLog.log(user_id, "add_course", f"Added: {name} ({cid})")

    @staticmethod
    def delete(cid: str, user_id: int):
        result = Database.execute("SELECT name FROM courses WHERE id = ?", (cid,), fetch=True)
        if not result:
            raise ValueError(f"Course {cid} not found")
        course_name = result[0][0]

        Database.execute("DELETE FROM courses WHERE id = ?", (cid,))
        ActivityLog.log(user_id, "delete_course", f"Deleted: {course_name} ({cid})")
        return course_name

    @staticmethod
    def delete_all(user_id: int):
        count = Database.execute("SELECT COUNT(*) FROM courses", fetch=True)[0][0]
        Database.execute("DELETE FROM courses")
        ActivityLog.log(user_id, "delete_all_courses", f"Deleted all {count} courses")
        return count

    @staticmethod
    def get_all() -> List[Tuple]:
        return Database.execute("SELECT * FROM courses ORDER BY semester, name", fetch=True)

class GradeManager:
    @staticmethod
    def calculate_letter(grade: float) -> str:
        if grade >= 90: return 'A'
        if grade >= 80: return 'B'
        if grade >= 70: return 'C'
        if grade >= 60: return 'D'
        return 'F'

    @staticmethod
    def grade_to_gpa_points(grade: float) -> float:
        if grade >= 90: return 4.0
        if grade >= 80: return 3.0
        if grade >= 70: return 2.0
        if grade >= 60: return 1.0
        return 0.0

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
            (sid, cid, grade, letter),
        )

        GradeManager.update_student_gpa(sid)
        ActivityLog.log(user_id, "add_grade", f"Grade {grade} for {sid} in {cid}")

    @staticmethod
    def update_student_gpa(sid: str):
        result = Database.execute("""
            SELECT g.grade, c.credits
            FROM grades g
            JOIN courses c ON c.id = g.course_id
            WHERE g.student_id = ?
        """, (sid,), fetch=True)

        if not result:
            return

        total_points = 0.0
        total_credits = 0
        for grade, credits in result:
            total_points += GradeManager.grade_to_gpa_points(grade) * credits
            total_credits += credits

        if total_credits > 0:
            gpa = total_points / total_credits
            Database.execute("UPDATE students SET gpa = ? WHERE id = ?", (round(gpa, 2), sid))

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
        results = []
        rankings = Analytics.get_gpa_rankings()
        for name, sid, gpa, courses in rankings or []:
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

class ImportExport:
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
                         row.get('major'), int(row.get('enrollment_year', 2024))),
                    )
                    count += 1
                except Exception:
                    pass
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
            writer.writerows(rows or [])

        ActivityLog.log(user_id, "export_report", f"Exported to {path}")
