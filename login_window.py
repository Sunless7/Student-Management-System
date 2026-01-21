import tkinter as tk
from tkinter import messagebox
from auth import Auth
from managers import ActivityLog

class LoginWindow:
    def __init__(self, root):
        self.root = root
        self.root.title("Academic System - Login")
        self.root.geometry("400x250")
        self.root.resizable(False, False)
        self.center_window()

        self.user_data = None
        self.setup_ui()

    def center_window(self):
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - 200
        y = (self.root.winfo_screenheight() // 2) - 125
        self.root.geometry(f"400x250+{x}+{y}")

    def setup_ui(self):
        frame = tk.Frame(self.root, padx=40, pady=40)
        frame.pack(expand=True)

        tk.Label(frame, text="Academic Performance System",
                 font=("Arial", 14, "bold")).grid(row=0, column=0, columnspan=2, pady=(0, 20))

        tk.Label(frame, text="Username:").grid(row=1, column=0, sticky="e", pady=5)
        self.username_entry = tk.Entry(frame, width=25)
        self.username_entry.grid(row=1, column=1, pady=5)

        tk.Label(frame, text="Password:").grid(row=2, column=0, sticky="e", pady=5)
        self.password_entry = tk.Entry(frame, width=25, show="*")
        self.password_entry.grid(row=2, column=1, pady=5)

        tk.Button(frame, text="Login", command=self.login, width=20,
                  bg="#4CAF50", fg="white").grid(row=3, column=0, columnspan=2, pady=(20, 5))

        tk.Label(frame, text="Default: admin / admin123",
                 font=("Arial", 8), fg="gray").grid(row=4, column=0, columnspan=2)

        self.password_entry.bind("<Return>", lambda e: self.login())
        self.username_entry.focus()

    def login(self):
        username = self.username_entry.get()
        password = self.password_entry.get()

        if not username or not password:
            messagebox.showerror("Error", "Please enter credentials")
            return

        user_data = Auth.authenticate(username, password)
        if user_data:
            self.user_data = user_data
            ActivityLog.log(user_data[0], "login", f"User logged in: {username}")
            self.root.destroy()
        else:
            messagebox.showerror("Error", "Invalid credentials")
            self.password_entry.delete(0, tk.END)
