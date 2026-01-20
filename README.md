# Academic Performance System

A desktop application for managing student records, courses, and grades with automatic GPA calculation.

## What This Does

This is a student management system that helps schools track students, courses, and grades. It automatically calculates GPAs on a 4.0 scale, identifies failing students, and generates reports.

## Main Features

### Students Tab
- **Add students** with ID, name, email, major, and enrollment year
- **Update student information** by selecting them from the table
- **Delete students** individually or all at once
- **Search students** by ID, name, or major
- **Import students** from CSV files
- **View transcripts** showing all courses and grades for a student
- **GPA displayed** on 4.0 scale (automatically calculated)

### Courses Tab
- **Add courses** with course ID, name, semester, credits (1-6), and instructor
- **Delete courses** individually or all at once
- **View course catalog** with all available courses

### Grades Tab
- **Record grades** (0-100) for students in courses
- **Automatic letter grade conversion**: A (90+), B (80-89), C (70-79), D (60-69), F (<60)
- **Automatic GPA calculation** on 4.0 scale based on course credits (weighted average)
- **See failing students** - anyone with grades below 60 shows up automatically

### Analytics Tab
- **GPA Rankings** - All students ranked by GPA (0.0-4.0 scale)
- **Academic Status** - Classifies students as:
  - Dean's List (GPA ≥ 3.5)
  - Good Standing (GPA ≥ 2.0)
  - Warning (GPA ≥ 1.0)
  - Academic Probation (GPA < 1.0)
- **Course Statistics** - Shows enrolled students (unique count), average grade, min, max grades per course
- **Export to CSV** - Save all data to a file

## How to Run

1. Make sure Python 3.7+ is installed
2. Run the program: `python final_project.py`
3. Login with:
   - Username: `admin`
   - Password: `admin123`

## How to Use

### Step 1: Add Students
1. Go to "Students" tab
2. Fill in ID (required) and Name (required)
3. Fill in email, major, year (optional)
4. Click "Add Student"

### Step 2: Add Courses
1. Go to "Courses" tab
2. Fill in Course ID, Name, Semester, Credits (1-6)
3. Click "Add Course"

### Step 3: Record Grades
1. Go to "Grades & Failing Students" tab
2. Enter Student ID, Course ID, and Grade (0-100)
3. Click "Record Grade"
4. The system automatically:
   - Converts to letter grade
   - Converts to GPA points (A=4.0, B=3.0, C=2.0, D=1.0, F=0.0)
   - Updates the student's GPA on 4.0 scale
   - Shows the student in failing list if grade < 60

### Step 4: View Reports
1. Go to "Analytics & Reports" tab
2. Click any button to see different reports
3. Use "Export Full Report" to save data to CSV

## How It Works (Technical)

### Database (SQLite)
The program stores data in a file called `academic.db` with these tables:

- **students** - Stores student info (ID, name, email, major, year, GPA on 4.0 scale, status)
- **courses** - Stores course info (ID, name, semester, credits, instructor)
- **grades** - Links students to courses with their numerical grades (0-100) and letter grades
- **users** - Login information with encrypted passwords
- **activity_log** - Tracks all actions for security

### Code Structure

**Database Layer** (`Database` class)
- Connects to SQLite database
- Executes SQL queries safely
- Creates tables on first run

**Business Logic** (Manager classes)
- `StudentManager` - Add, update, delete, search students
- `CourseManager` - Add, delete courses
- `GradeManager` - Record grades, calculate letter grades, convert to GPA on 4.0 scale
- `Analytics` - Generate reports
- `Auth` - Handle login with password encryption (SHA-256)

**User Interface** (Tkinter)
- `LoginWindow` - Login screen
- `AcademicApp` - Main application with tabs

### Key Features Explained

**GPA Calculation (4.0 Scale)**
- Numerical grades (0-100) are converted to GPA points:
  - A (90-100) = 4.0 points
  - B (80-89) = 3.0 points
  - C (70-79) = 2.0 points
  - D (60-69) = 1.0 points
  - F (0-59) = 0.0 points
- Weighted average based on course credits
- Formula: (GPA_Points1 × Credits1 + GPA_Points2 × Credits2) / Total Credits
- Example: Student gets A (4.0) in 3-credit course and B (3.0) in 3-credit course
  - GPA = (4.0×3 + 3.0×3) / 6 = 21/6 = 3.5
- Updates automatically whenever a grade is added

**Data Validation**
- Checks email format with regex
- Ensures grades are 0-100
- Verifies student and course exist before adding grades
- Prevents duplicate student IDs
- Leading zeros in IDs are preserved (0909 stays as 0909)

**Security**
- Passwords are encrypted (SHA-256 hash)
- SQL injection prevented with parameterized queries
- All actions are logged with timestamps

**Cascading Deletes**
- Delete a student → all their grades are deleted too
- Delete a course → all grades for that course are deleted too
- Delete all courses → all student GPAs reset to 0.0
- Keeps database consistent

**Course Enrollment Count**
- Counts unique students per course (not total grade records)
- If 1 student takes 4 courses, each course shows "1 enrolled"

## CSV Import Format

To import multiple students at once, create a CSV file like this:

```csv
id,name,email,major,enrollment_year
S001,John Doe,john@email.com,Computer Science,2024
S002,Jane Smith,jane@email.com,Mathematics,2024
0909,Mari,mari@email.com,Computer Science,2024
```

Then click "Import CSV" in the Students tab.

## Important Notes

- The database file `academic.db` is created automatically
- Don't edit the database file directly
- **GPA is on 4.0 scale** (not 0-100)
- **Grades are 0-100** (get converted to GPA points)
- Leading zeros in IDs are preserved (0909 stays as 0909)
- Deleting students or courses also deletes their grades
- Delete operations cannot be undone (requires double confirmation)
- Course statistics show unique student enrollment count

## System Requirements

- Python 3.7 or higher
- Tkinter (usually comes with Python)
- SQLite3 (comes with Python)
- Works on Windows, Mac, Linux
