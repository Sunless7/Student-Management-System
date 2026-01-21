import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from database import Database
from managers import (
    StudentManager, CourseManager, GradeManager, Analytics, ImportExport
)

class AcademicApp:
    def __init__(self, root, user_data):
        self.root = root
        self.user_id, self.username, self.role = user_data

        self.root.title(f"Academic System - {self.username} ({self.role})")
        self.root.geometry("1200x700")

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

        self.setup_students_tab()
        self.setup_courses_tab()
        self.setup_grades_tab()
        self.setup_analytics_tab()

        status = tk.Label(self.root, text=f"Logged in as {self.username}",
                          relief=tk.SUNKEN, anchor="w", bg="#f0f0f0")
        status.pack(side=tk.BOTTOM, fill=tk.X)

    # ---------- tabs ----------
    def setup_students_tab(self):
        tab = tk.Frame(self.notebook)
        self.notebook.add(tab, text="Students")

        left = tk.Frame(tab, padx=10, pady=10)
        left.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(left, text="Student Management", font=("Arial", 12, "bold")).pack(pady=(0, 10))

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

        tk.Button(left, text="Add Student", command=self.add_student, bg="#4CAF50", fg="white").pack(fill=tk.X, pady=2)
        tk.Button(left, text="Update Selected", command=self.update_student, bg="#2196F3", fg="white").pack(fill=tk.X, pady=2)
        tk.Button(left, text="Delete Selected", command=self.delete_student, bg="#F44336", fg="white").pack(fill=tk.X, pady=2)
        tk.Button(left, text="Delete All Students", command=self.delete_all_students, bg="#B71C1C", fg="white").pack(fill=tk.X, pady=2)
        tk.Button(left, text="View Transcript", command=self.view_transcript, bg="#FF9800", fg="white").pack(fill=tk.X, pady=2)
        tk.Button(left, text="Clear Fields", command=self.clear_student_fields, bg="#607D8B", fg="white").pack(fill=tk.X, pady=2)
        tk.Button(left, text="Import CSV", command=self.import_students, bg="#9C27B0", fg="white").pack(fill=tk.X, pady=(15, 2))

        right = tk.Frame(tab)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        search_frame = tk.Frame(right)
        search_frame.pack(fill=tk.X, pady=(0, 5))
        tk.Label(search_frame, text="Search:").pack(side=tk.LEFT)
        self.student_search = tk.StringVar()
        tk.Entry(search_frame, textvariable=self.student_search, width=30).pack(side=tk.LEFT, padx=5)
        tk.Button(search_frame, text="Search", command=self.search_students).pack(side=tk.LEFT)
        tk.Button(search_frame, text="Show All", command=self.load_students).pack(side=tk.LEFT, padx=5)

        self.students_tree = ttk.Treeview(
            right,
            columns=("ID", "Name", "Email", "Major", "Year", "GPA", "Status"),
            show="headings", height=25
        )
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

        left = tk.Frame(tab, padx=10, pady=10)
        left.pack(side=tk.LEFT, fill=tk.Y)

        tk.Label(left, text="Course Management", font=("Arial", 12, "bold")).pack(pady=(0, 10))

        self.course_entries = {}
        for label, key in [("Course ID*:", "id"), ("Course Name*:", "name"),
                           ("Semester*:", "semester"), ("Credits (1-6)*:", "credits"),
                           ("Instructor:", "instructor")]:
            tk.Label(left, text=label).pack(anchor="w")
            entry = tk.Entry(left, width=30)
            entry.pack(pady=(0, 5))
            self.course_entries[key] = entry

        tk.Button(left, text="Add Course", command=self.add_course, bg="#4CAF50", fg="white").pack(fill=tk.X, pady=2)
        tk.Button(left, text="Delete Selected", command=self.delete_course, bg="#F44336", fg="white").pack(fill=tk.X, pady=2)
        tk.Button(left, text="Delete All Courses", command=self.delete_all_courses, bg="#B71C1C", fg="white").pack(fill=tk.X, pady=2)
        tk.Button(left, text="Clear Fields", command=self.clear_course_fields, bg="#607D8B", fg="white").pack(fill=tk.X, pady=2)

        right = tk.Frame(tab)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(right, text="Available Courses", font=("Arial", 11, "bold")).pack(pady=(0, 5))

        self.courses_tree = ttk.Treeview(
            right,
            columns=("ID", "Name", "Semester", "Credits", "Instructor", "Capacity"),
            show="headings", height=25
        )
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

        tk.Button(left, text="Record Grade", command=self.add_grade, bg="#4CAF50", fg="white").pack(fill=tk.X)

        right = tk.Frame(tab)
        right.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)

        tk.Label(right, text="Failing Students (Grade < 60)", font=("Arial", 11, "bold")).pack(pady=(0, 5))

        self.failing_tree = ttk.Treeview(
            right,
            columns=("Student", "ID", "Email", "Course", "Grade", "Letter"),
            show="headings", height=25
        )
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

        tk.Button(btn_frame, text="Show GPA Rankings", command=self.show_gpa_rankings, bg="#2196F3", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Academic Status Report", command=self.show_academic_status, bg="#FF9800", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Course Statistics", command=self.show_course_stats, bg="#9C27B0", fg="white").pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Export Full Report", command=self.export_report, bg="#4CAF50", fg="white").pack(side=tk.LEFT, padx=5)

        self.analytics_tree = ttk.Treeview(tab, show="headings", height=30)
        scrollbar = ttk.Scrollbar(tab, orient=tk.VERTICAL, command=self.analytics_tree.yview)
        self.analytics_tree.configure(yscrollcommand=scrollbar.set)

        self.analytics_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)

    # ---------- data loading ----------
    def load_data(self):
        self.load_students()
        self.load_courses()
        self.load_failing_students()

    def load_students(self):
        self.students_tree.delete(*self.students_tree.get_children())
        for row in StudentManager.get_all() or []:
            row_list = list(row)
            row_list[0] = str(row_list[0])
            self.students_tree.insert("", tk.END, values=row_list)

    def load_courses(self):
        self.courses_tree.delete(*self.courses_tree.get_children())
        for row in CourseManager.get_all() or []:
            self.courses_tree.insert("", tk.END, values=row)

    def load_failing_students(self):
        self.failing_tree.delete(*self.failing_tree.get_children())
        for row in GradeManager.get_failing_students() or []:
            self.failing_tree.insert("", tk.END, values=row)

    def search_students(self):
        query = self.student_search.get()
        if not query:
            self.load_students()
            return
        self.students_tree.delete(*self.students_tree.get_children())
        for row in StudentManager.search(query) or []:
            row_list = list(row)
            row_list[0] = str(row_list[0])
            self.students_tree.insert("", tk.END, values=row_list)

    # ---------- student actions ----------
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

        values = self.students_tree.item(selected[0])['values']
        student_id = values[0]
        student_name = values[1]

        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete student:\n\nID: {student_id}\nName: {student_name}\n\n"
            f"This will also delete all their grades!\nThis action cannot be undone."
        )
        if confirm:
            try:
                deleted_name = StudentManager.delete(student_id, self.user_id)
                messagebox.showinfo("Success", f"Student '{deleted_name}' deleted successfully")
                self.load_students()
                self.load_failing_students()
                self.clear_student_fields()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def delete_all_students(self):
        student_count = len(self.students_tree.get_children())
        if student_count == 0:
            messagebox.showinfo("Info", "There are no students to delete")
            return

        confirm = messagebox.askyesno(
            "⚠️ WARNING: Delete All Students ⚠️",
            f"You are about to DELETE ALL {student_count} STUDENTS!\n\nTHIS CANNOT BE UNDONE!\n\nContinue?",
            icon='warning'
        )
        if not confirm:
            return

        double_confirm = messagebox.askyesno("Final Confirmation", "Final warning. Continue?", icon='warning')
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
        if not selected:
            return
        values = self.students_tree.item(selected[0])['values']
        for entry in self.student_entries.values():
            entry.delete(0, tk.END)

        self.student_entries["id"].insert(0, str(values[0]))
        self.student_entries["name"].insert(0, str(values[1]))
        self.student_entries["email"].insert(0, str(values[2]) if values[2] else "")
        self.student_entries["major"].insert(0, str(values[3]) if values[3] else "")
        self.student_entries["year"].insert(0, str(values[4]) if values[4] else "")
        self.student_status.set(values[6])

    def clear_student_fields(self):
        for entry in self.student_entries.values():
            entry.delete(0, tk.END)

    # ---------- course actions ----------
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
        if not selected:
            return
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

        values = self.courses_tree.item(selected[0])['values']
        course_id = values[0]
        course_name = values[1]

        confirm = messagebox.askyesno(
            "Confirm Deletion",
            f"Are you sure you want to delete course:\n\nID: {course_id}\nName: {course_name}\n\n"
            f"This will also delete all grades for this course!\nThis action cannot be undone."
        )
        if confirm:
            try:
                deleted_name = CourseManager.delete(course_id, self.user_id)
                messagebox.showinfo("Success", f"Course '{deleted_name}' deleted successfully")
                self.load_courses()
                self.load_failing_students()
                self.load_students()
                self.clear_course_fields()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    def delete_all_courses(self):
        course_count = len(self.courses_tree.get_children())
        if course_count == 0:
            messagebox.showinfo("Info", "There are no courses to delete")
            return

        confirm = messagebox.askyesno(
            "⚠️ WARNING: Delete All Courses ⚠️",
            f"You are about to DELETE ALL {course_count} COURSES!\n\nTHIS CANNOT BE UNDONE!\n\nContinue?",
            icon='warning'
        )
        if not confirm:
            return

        double_confirm = messagebox.askyesno("Final Confirmation", "Final warning. Continue?", icon='warning')
        if double_confirm:
            try:
                count = CourseManager.delete_all(self.user_id)
                Database.execute("UPDATE students SET gpa = 0.0")
                messagebox.showinfo("Complete", f"Successfully deleted all {count} courses and their grades")
                self.load_courses()
                self.load_students()
                self.load_failing_students()
                self.clear_course_fields()
            except Exception as e:
                messagebox.showerror("Error", str(e))

    # ---------- transcript ----------
    def view_transcript(self):
        sid = self.student_entries["id"].get()
        if not sid:
            messagebox.showwarning("Warning", "Please enter a student ID")
            return

        transcript = StudentManager.get_transcript(sid)
        if not transcript:
            messagebox.showinfo("Info", "No grades found for this student")
            return

        popup = tk.Toplevel(self.root)
        popup.title(f"Transcript - {sid}")
        popup.geometry("800x400")

        tree = ttk.Treeview(
            popup,
            columns=("Course", "Semester", "Credits", "Grade", "Letter", "Date"),
            show="headings", height=15
        )
        for col in tree["columns"]:
            tree.heading(col, text=col)
            tree.column(col, width=120)

        for row in transcript:
            tree.insert("", tk.END, values=row)

        tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # ---------- grades ----------
    def add_grade(self):
        try:
            student_id = self.grade_student.get().strip()
            course_id = self.grade_course.get().strip()
            grade_value = self.grade_value.get().strip()

            if not student_id:
                messagebox.showerror("Error", "Please enter a Student ID")
                return
            if not course_id:
                messagebox.showerror("Error", "Please enter a Course ID")
                return
            if not grade_value:
                messagebox.showerror("Error", "Please enter a grade value")
                return

            if not Database.execute("SELECT id FROM students WHERE id = ?", (student_id,), fetch=True):
                messagebox.showerror("Error", f"Student ID '{student_id}' does not exist!")
                return
            if not Database.execute("SELECT id FROM courses WHERE id = ?", (course_id,), fetch=True):
                messagebox.showerror("Error", f"Course ID '{course_id}' does not exist!")
                return

            GradeManager.add(student_id, course_id, float(grade_value), self.user_id)
            messagebox.showinfo("Success", f"Grade {grade_value} recorded for {student_id} in {course_id}")
            self.load_failing_students()
            self.load_students()
            self.grade_student.delete(0, tk.END)
            self.grade_course.delete(0, tk.END)
            self.grade_value.delete(0, tk.END)
        except ValueError as ve:
            messagebox.showerror("Error", str(ve))
        except Exception as e:
            messagebox.showerror("Error", f"Failed to record grade: {str(e)}")

    # ---------- import/export ----------
    def import_students(self):
        path = filedialog.askopenfilename(title="Select CSV File", filetypes=[("CSV Files", "*.csv")])
        if path:
            try:
                count = ImportExport.import_students_csv(path, self.user_id)
                messagebox.showinfo("Success", f"Imported {count} students")
                self.load_students()
            except Exception as e:
                messagebox.showerror("Error", str(e))

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

    # ---------- analytics ----------
    def show_gpa_rankings(self):
        self.analytics_tree.delete(*self.analytics_tree.get_children())
        self.analytics_tree["columns"] = ("Name", "ID", "GPA", "Courses")
        for col in self.analytics_tree["columns"]:
            self.analytics_tree.heading(col, text=col)
            self.analytics_tree.column(col, width=150 if col == "Name" else 100)
        for row in Analytics.get_gpa_rankings() or []:
            self.analytics_tree.insert("", tk.END, values=row)

    def show_academic_status(self):
        self.analytics_tree.delete(*self.analytics_tree.get_children())
        self.analytics_tree["columns"] = ("Name", "ID", "GPA", "Courses", "Status")
        for col in self.analytics_tree["columns"]:
            self.analytics_tree.heading(col, text=col)
            self.analytics_tree.column(col, width=150 if col == "Name" else 100)
        for row in Analytics.get_academic_status() or []:
            self.analytics_tree.insert("", tk.END, values=row)

    def show_course_stats(self):
        self.analytics_tree.delete(*self.analytics_tree.get_children())
        self.analytics_tree["columns"] = ("Course", "Semester", "Enrolled", "Avg Grade", "Min Grade", "Max Grade")
        for col in self.analytics_tree["columns"]:
            self.analytics_tree.heading(col, text=col)
            self.analytics_tree.column(col, width=150 if col == "Course" else 100)
        for row in Analytics.get_course_statistics() or []:
            self.analytics_tree.insert("", tk.END, values=row)
