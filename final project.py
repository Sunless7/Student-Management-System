students = {}

def add_student():
    student_id = input("Enter student ID: ")
    if student_id in students:
        print("Student already exists.")
        return
    name = input("Enter student name: ")
    grade = input("Enter student grade: ")
    students[student_id] = {"name": name, "grade": grade}
    print("Student added.")

def view_students():
    if not students:
        print("No students found.")
        return
    for sid, info in students.items():
        print(f"ID: {sid} | Name: {info['name']} | Grade: {info['grade']}")

def update_student():
    student_id = input("Enter student ID to update: ")
    if student_id not in students:
        print("Student not found.")
        return
    new_grade = input("Enter new grade: ")
    students[student_id]["grade"] = new_grade
    print("Grade updated.")

def delete_student():
    student_id = input("Enter student ID to delete: ")
    if student_id not in students:
        print("Student not found.")
        return
    del students[student_id]
    print("Student deleted.")

def menu():
    while True:
        print("\n1. Add Student")
        print("2. View Students")
        print("3. Update Student Grade")
        print("4. Delete Student")
        print("5. Exit")

        choice = input("Choose an option: ")

        if choice == "1":
            add_student()
        elif choice == "2":
            view_students()
        elif choice == "3":
            update_student()
        elif choice == "4":
            delete_student()
        elif choice == "5":
            print("Exiting program.")
            break
        else:
            print("Invalid choice.")

menu()
