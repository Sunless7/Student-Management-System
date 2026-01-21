import tkinter as tk

from database import Database
from login_window import LoginWindow
from app_window import AcademicApp

def main():
    Database.init_db()

    # 1) Login window
    root = tk.Tk()
    login = LoginWindow(root)
    root.mainloop()

    if login.user_data:
        app_root = tk.Tk()
        AcademicApp(app_root, login.user_data)
        app_root.mainloop()

if __name__ == "__main__":
    main()
