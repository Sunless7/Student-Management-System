import sqlite3
import tkinter as tk
from tkinter import messagebox, filedialog
import csv

# ---------------- DATABASE SETUP ----------------

conn = sqlite3.connect("school.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS students (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS courses (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    semester TEXT NOT NULL
)
""")

cursor.execute("""
CREATE TABLE IF NOT EXISTS grades (
    student_id TEXT,
    course_id TEXT,
    grade REAL,
    FOREIGN KEY(student_id) REFERENCES students(id),
    FOREIGN KEY(course_id) REFERENCES courses(id)
)
""")

conn.commit()

# ---------------- BACKEND LOGIC ----------------

def add_student():
    sid = student_id.get()
    name = student_name.get()
    if not sid or not name:
        messagebox.showerror("Error", "Missing student data")
        return
    try:
        cursor.execute("INSERT INTO students VALUES (?,?)", (sid, name))
        conn.commit()
        messagebox.showinfo("Success", "Student added")
    except:
        messagebox.showerror("Error", "Student already exists")

def add_course():
    cid = course_id.get()
    name = course_name.get()
    sem = semester.get()
    if not cid or not name or not sem:
        messagebox.showerror("Error", "Missing course data")
        return
    try:
        cursor.execute("INSERT INTO courses VALUES (?,?,?)", (cid, name, sem))
        conn.commit()
        messagebox.showinfo("Success", "Course added")
    except:
        messagebox.showerror("Error", "Course already exists")

def add_grade():
    sid = student_id.get()
    cid = course_id.get()
    try:
        g = float(grade.get())
        cursor.execute("INSERT INTO grades VALUES (?,?,?)", (sid, cid, g))
        conn.commit()
        messagebox.showinfo("Success", "Grade added")
    except:
        messagebox.showerror("Error", "Invalid data")

def average_per_course():
    cursor.execute("""
        SELECT courses.name, AVG(grades.grade)
        FROM grades
        JOIN courses ON grades.course_id = courses.id
        GROUP BY courses.id
    """)
    rows = cursor.fetchall()
    show_results(rows)

def ranking_students():
    cursor.execute("""
        SELECT students.name, AVG(grades.grade) AS avg_grade
        FROM grades
        JOIN students ON grades.student_id = students.id
        GROUP BY students.id
        ORDER BY avg_grade DESC
    """)
    rows = cursor.fetchall()
    show_results(rows)

def filter_by_semester():
    sem = semester.get()
    cursor.execute("""
        SELECT students.name, courses.name, grades.grade
        FROM grades
        JOIN students ON grades.student_id = students.id
        JOIN courses ON grades.course_id = courses.id
        WHERE courses.semester = ?
    """, (sem,))
    rows = cursor.fetchall()
    show_results(rows)

def import_students_csv():
    file = filedialog.askopenfilename(filetypes=[("CSV files","*.csv")])
    if not file:
        return
    with open(file) as f:
        reader = csv.reader(f)
        for row in reader:
            cursor.execute("INSERT OR IGNORE INTO students VALUES (?,?)", (row[0], row[1]))
    conn.commit()
    messagebox.showinfo("Success", "Students imported")

def export_report():
    file = filedialog.asksaveasfilename(defaultextension=".csv")
    if not file:
        return
    cursor.execute("""
        SELECT students.name, courses.name, grades.grade
        FROM grades
        JOIN students ON grades.student_id = students.id
        JOIN courses ON grades.course_id = courses.id
    """)
    rows = cursor.fetchall()
    with open(file, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["Student", "Course", "Grade"])
        writer.writerows(rows)
    messagebox.showinfo("Success", "Report exported")

def show_results(rows):
    if not rows:
        messagebox.showinfo("Result", "No data")
        return
    text = ""
    for r in rows:
        text += " | ".join(map(str, r)) + "\n"
    messagebox.showinfo("Result", text)

# ---------------- FRONTEND ----------------

root = tk.Tk()
root.title("Student Management System")
root.geometry("400x500")

tk.Label(root, text="Student ID").pack()
student_id = tk.Entry(root)
student_id.pack()

tk.Label(root, text="Student Name").pack()
student_name = tk.Entry(root)
student_name.pack()

tk.Label(root, text="Course ID").pack()
course_id = tk.Entry(root)
course_id.pack()

tk.Label(root, text="Course Name").pack()
course_name = tk.Entry(root)
course_name.pack()

tk.Label(root, text="Semester").pack()
semester = tk.Entry(root)
semester.pack()

tk.Label(root, text="Grade").pack()
grade = tk.Entry(root)
grade.pack()

tk.Button(root, text="Add Student", command=add_student).pack(pady=2)
tk.Button(root, text="Add Course", command=add_course).pack(pady=2)
tk.Button(root, text="Add Grade", command=add_grade).pack(pady=2)

tk.Button(root, text="Average Grade Per Course", command=average_per_course).pack(pady=2)
tk.Button(root, text="Student Ranking", command=ranking_students).pack(pady=2)
tk.Button(root, text="Filter By Semester", command=filter_by_semester).pack(pady=2)

tk.Button(root, text="Import Students (CSV)", command=import_students_csv).pack(pady=2)
tk.Button(root, text="Export Report", command=export_report).pack(pady=2)

root.mainloop()
