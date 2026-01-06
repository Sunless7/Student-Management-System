Problem Statement

Manual tracking of students and grades is error-prone. This program provides a simple system to store, view, update, and delete student records using a menu-driven interface.

Features

Add a student (ID, name, grade)

View all students

Update a student’s grade

Delete a student

Prevents duplicate student IDs

Runs continuously until user exits

Data Structure

Uses a dictionary

Key: student_id

Value: another dictionary containing name and grade

Example:

{
  "101": {"name": "John", "grade": "85"},
  "102": {"name": "Ana", "grade": "92"}
}

Program Structure

add_student() – validates and inserts data

view_students() – iterates and displays records

update_student() – modifies existing data

delete_student() – removes records

menu() – controls program flow using a loop

Each function has a single responsibility.

Concepts Demonstrated

Variables and data types

Dictionaries

Functions

Loops (while)

Conditionals (if/elif/else)

Input validation

Modular program design

How It Works (Execution Flow)

Program starts and shows menu

User selects an option

Corresponding function executes

Program returns to menu

Ends only when user selects Exit

Limitations

Data is stored in memory only

Data resets when program closes

Console-based (no GUI)

These are intentional to keep the system simple and focused.

Conclusion

This project demonstrates core programming fundamentals and basic system design. It solves a real problem at an appropriate complexity level for an introductory computer science course.
