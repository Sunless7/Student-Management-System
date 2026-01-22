# Academic Performance System

A desktop application for managing student records, courses, and grades with automatic GPA calculation.  
Built using **Python**, **Tkinter**, and **SQLite**.

---

## Overview

This project allows schools or instructors to:

- Manage students and courses
- Record grades and automatically calculate GPA (4.0 scale)
- Detect failing students
- View analytics and reports
- Import/export data using CSV
- Track user activity

The application uses a graphical user interface (GUI) and a local SQLite database created automatically on first run.

---

## Features

- User authentication (admin / teacher / student roles)
- Student management (add, update, delete, search, transcript view)
- Course management
- Grade recording with GPA calculation
- Failing students list
- Analytics:
  - GPA rankings
  - Academic status classification
  - Course statistics
- CSV import/export
- Activity logging
- Clean separation of logic into multiple files (modular design)
- Automatic student ID generation (no manual ID input required)


---

## Project Structure

All files are located in the **project root directory**:

main.py # Entry point of the application
database.py # SQLite database setup and queries
auth.py # Authentication and password hashing
managers.py # Business logic (students, courses, grades, analytics)
login_window.py # Login window UI
app_window.py # Main application UI


---

## Requirements

- Python 3.9 or newer
- No external libraries required  
  (only standard library modules are used)

---

## How to Run (IMPORTANT)

The application must be run from the project root directory
(the folder where `main.py` is located).

### Steps

1. Clone the repository:
   git clone https://github.com/Sunless7/Student-Management-System.git

2. Enter the project folder:
   cd Student-Management-System

3. Run the application:
   python main.py
   (or)
   py main.py


## Window Behavior

- After successful login, the main application window opens maximized.
- The layout automatically adapts to screen resolution.
- No manual resizing is required.


Login Credentials

A default admin account is created automatically on first run:

Username: admin

Password: admin123
