import tkinter as tk
from database import Database
from login_window import LoginWindow
from app_window import AcademicApp

def main():
    Database.init_db()

    # login
    root = tk.Tk()
    login = LoginWindow(root)
    root.mainloop()

    # app
    if login.user_data:
        app_root = tk.Tk()

        # maximize NOW (Windows)
        app_root.update_idletasks()
        try:
            app_root.state("zoomed")
        except Exception:
            sw = app_root.winfo_screenwidth()
            sh = app_root.winfo_screenheight()
            app_root.geometry(f"{sw}x{sh}+0+0")

        AcademicApp(app_root, login.user_data)
        app_root.mainloop()

if __name__ == "__main__":
    main()
