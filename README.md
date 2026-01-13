# Student Management System

## Overview

This project is a **desktop Student Management System** built with **Python**, featuring a **graphical user interface**, a **persistent relational database**, and a clear separation between frontend, backend, and data layers.

The goal of the project is to demonstrate core computer science concepts such as **data modeling**, **database relationships**, **SQL queries**, and **application architecture**.

---

## Architecture

The system is structured into three layers:

* **Frontend**: Tkinter GUI for user interaction
* **Backend**: Python functions implementing application logic
* **Database**: SQLite relational database for persistent storage

**Data flow**:
User → GUI → Backend Logic → SQLite Database → GUI Output

---

## Database Design

The application uses a **relational SQLite database** (`school.db`) with multiple tables and defined relationships.

### Tables

* **students**

  * `id` (PRIMARY KEY)
  * `name`

* **courses**

  * `id` (PRIMARY KEY)
  * `name`
  * `semester`

* **grades**

  * `student_id` (FOREIGN KEY → students.id)
  * `course_id` (FOREIGN KEY → courses.id)
  * `grade`

This design avoids data duplication and allows meaningful queries across related entities.

---

## Features

* Add students, courses, and grades
* Persistent data storage using SQLite
* Relational queries using JOINs
* **Average grade per course**
* **Student ranking by average grade**
* **Filtering results by semester**
* Import students from CSV file
* Export generated reports to CSV
* Simple and clear graphical interface

---

## Key Concepts Demonstrated

* Relational database modeling
* Primary and foreign keys
* SQL aggregation (`AVG`, `GROUP BY`)
* Sorting and ranking (`ORDER BY`)
* Filtering (`WHERE`)
* CRUD operations
* Separation of concerns (UI vs logic vs data)
* File import/export (CSV)

---

## Why This Project

This project goes beyond a basic console CRUD application by introducing:

* A real database instead of in-memory storage
* Multiple related tables instead of a single flat structure
* Computed data (averages, rankings)
* A graphical frontend instead of terminal input

It reflects how real-world applications manage structured data.

---

## Limitations

* Desktop-only application
* Basic UI without advanced validation
* Single-user local database

These limitations are intentional to keep the project focused and understandable.

---

## Possible Improvements

* Search functionality
* Advanced input validation
* User authentication
* Web-based frontend
* Data visualization

---

## Technologies Used

* Python 3
* SQLite
* Tkinter
* CSV module
