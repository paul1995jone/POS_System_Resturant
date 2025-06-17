# ui/login_page.py
import tkinter as tk
from tkinter import messagebox
from ui.user_page import open_user_dashboard
from ui.admin_page import open_admin_dashboard
from utils.Shared_functions import record_daily_history_if_needed, execute_query


def check_credentials(username, password, root):
    result = execute_query(
        "SELECT role FROM users WHERE username=? AND password=?",
        params=(username, password),
        fetchone=True
    )

    if result:
        role = result[0]
        messagebox.showinfo("Login Successful", f"Welcome, {username} ({role})!")

        root.withdraw()  # Close login window

        if role == "admin":
            open_admin_dashboard(root)
        elif role == "user":
            record_daily_history_if_needed()
            open_user_dashboard(root)
    else:
        messagebox.showerror("Login Failed", "Invalid username or password")


def open_login_window():
    root = tk.Tk()
    root.title("Boikunther Adda Billing System - Login")
    root.geometry("400x200")

    tk.Label(root, text="Username:").pack(pady=5)
    username_entry = tk.Entry(root)
    username_entry.pack()

    tk.Label(root, text="Password:").pack(pady=5)
    password_entry = tk.Entry(root, show="*")
    password_entry.pack()

    def on_login(event=None):
        username = username_entry.get()
        password = password_entry.get()
        check_credentials(username, password, root)

    login_button = tk.Button(root, text="Login", command=on_login)
    login_button.pack(pady=10)

    # Focus on username field initially
    username_entry.focus_set()

    # Bind Enter key to login for all widgets
    root.bind("<Return>", on_login)

    root.mainloop()
