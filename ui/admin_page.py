# ui/admin_page.py

import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from utils.Shared_functions import execute_query, resource_path
import os, csv


def open_admin_dashboard(root):
    root.withdraw()
    admin_win = tk.Toplevel()
    admin_win.title("Boikunther Adda - Admin Dashboard")
    admin_win.geometry("800x400")
    admin_win.protocol("WM_DELETE_WINDOW", root.quit)

    # Treeview to show items
    columns = ("ID", "Name", "Price", "Available", "Category")
    # Create a frame for the Treeview and scrollbars
    tree_frame = tk.Frame(admin_win)
    tree_frame.pack(fill=tk.BOTH, expand=True)

    # Add Scrollbars
    scroll_y = tk.Scrollbar(tree_frame, orient=tk.VERTICAL)
    scroll_x = tk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)

    tree = ttk.Treeview(tree_frame, columns=columns, show="headings",
                        yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)

    scroll_y.config(command=tree.yview)
    scroll_y.pack(side=tk.RIGHT, fill=tk.Y)

    scroll_x.config(command=tree.xview)
    scroll_x.pack(side=tk.BOTTOM, fill=tk.X)

    tree.pack(fill=tk.BOTH, expand=True)

    # Define headings and column widths
    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=150, anchor=tk.CENTER)

    def load_items():
        tree.delete(*tree.get_children())
        for row in execute_query("SELECT id, name, price, is_available, category FROM items", fetch=True):
            tree.insert("", tk.END, values=row)

    load_items()

    # csv file related things
    CSV_FILE = resource_path("Item_history.csv")
    FIXED_HEADERS = ["Serial No", "Date", "Occasion", "Weather"]

    def ensure_csv_headers_exist():
        if not os.path.exists(CSV_FILE):
            with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(FIXED_HEADERS)

    def add_item_column(item_name):
        ensure_csv_headers_exist()

        with open(CSV_FILE, "r", newline="", encoding="utf-8") as f:
            reader = list(csv.reader(f))
            headers = reader[0]
            rows = reader[1:]

        if item_name not in headers:
            headers.append(item_name)
            for row in rows:
                row.append("")  # Add blank column to existing rows

            with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)

    def rename_item_column(old_name, new_name):
        ensure_csv_headers_exist()

        with open(CSV_FILE, "r", newline="", encoding="utf-8") as f:
            reader = list(csv.reader(f))
            headers = reader[0]
            rows = reader[1:]

        if old_name in headers:
            headers = [new_name if h == old_name else h for h in headers]

            with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow(headers)
                writer.writerows(rows)

    # def delete_item_column(item_name):
    #     ensure_csv_headers_exist()
    #     with open(CSV_FILE, "r", newline="", encoding="utf-8") as f:
    #         reader = csv.reader(f)
    #         headers = next(reader)
    #
    #     if item_name in headers:
    #         headers = [h for h in headers if h != item_name]
    #
    #         with open(CSV_FILE, "w", newline="", encoding="utf-8") as f:
    #             writer = csv.writer(f)
    #             writer.writerow(headers)

    # Add item to inventory list.
    def add_item():
        add_win = tk.Toplevel(admin_win)
        add_win.title("Add Item")
        add_win.geometry("300x250")
        add_win.grab_set()
        add_win.transient(admin_win)
        add_win.focus_set()

        tk.Label(add_win, text="Name").pack(pady=5)
        name_entry = tk.Entry(add_win)
        name_entry.pack()

        tk.Label(add_win, text="Price").pack(pady=5)
        price_entry = tk.Entry(add_win)
        price_entry.pack()

        # Add category dropdown
        tk.Label(add_win, text="Category").pack(pady=5)
        category_var = tk.StringVar(value="veg")
        tk.OptionMenu(add_win, category_var, "veg", "non-veg").pack()

        def save_item():
            name = name_entry.get()
            price = price_entry.get()
            category = category_var.get()
            if not name or not price:
                messagebox.showerror("Error", "Please fill all fields.")
                return
            try:
                price = float(price)
            except ValueError:
                messagebox.showerror("Error", "Invalid price.")
                return

            # Check for duplicate item name (case-insensitive)
            existing = execute_query("SELECT 1 FROM items WHERE REPLACE(LOWER(name), ' ', '') = ?", (name.replace(" ","").lower(),), fetchone=True)
            if existing:
                messagebox.showerror("Error", f"Item '{name}' already exists.")
                return

            # Insert into database
            execute_query("""INSERT INTO items (name, price, is_available, category)
                VALUES (?, ?, 1, ?)""", params=(name, price, category), commit=True)
            add_item_column(name)
            messagebox.showinfo("Success", "Item added successfully!")
            load_items()
            # Clear input fields instead of closing the window
            name_entry.delete(0, tk.END)
            price_entry.delete(0, tk.END)
            category_var.set("veg")  # Reset category to default
            name_entry.focus_set()  # Set focus back to name field
            load_items()  # Refresh the list in dashboard

        tk.Button(add_win, text="Save Item", command=save_item).pack(pady=10)

    # Delete item from inventory list.
    def delete_item():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Please select an item to delete.")
            return

        confirm = messagebox.askyesno("Confirm Delete", "Are you sure you want to delete this item?")
        if not confirm:
            return

        item_id = tree.item(selected[0])["values"][0]

        # Delete from database
        item = execute_query("SELECT name FROM items WHERE id = ?", (item_id,), fetchone=True)
        execute_query("DELETE FROM items WHERE id = ?", (item_id,), commit=True)
        # if item:
        #     item_name = item[0]
        #     delete_item_column(item_name)
        load_items()
        messagebox.showinfo("Deleted", "Item deleted successfully.")

    # Update item from inventory list.
    def edit_item():
        selected = tree.selection()
        if not selected:
            messagebox.showwarning("No selection", "Please select an item to edit.")
            return

        values = tree.item(selected[0])["values"]
        item_id, current_name, current_price, current_availability, current_category = values

        edit_win = tk.Toplevel(admin_win)
        edit_win.title("Edit Item")
        edit_win.geometry("300x300")

        tk.Label(edit_win, text="Name").pack(pady=5)
        name_entry = tk.Entry(edit_win)
        name_entry.insert(0, current_name)
        name_entry.pack()

        tk.Label(edit_win, text="Price").pack(pady=5)
        price_entry = tk.Entry(edit_win)
        price_entry.insert(0, str(current_price))
        price_entry.pack()

        tk.Label(edit_win, text="Category").pack(pady=5)
        category_var = tk.StringVar(value=current_category)
        tk.OptionMenu(edit_win, category_var, "Veg", "Non-Veg").pack()

        def save_changes():
            new_name = name_entry.get()
            new_price = price_entry.get()
            new_category = category_var.get()

            if not new_name or not new_price or not new_category:
                messagebox.showerror("Error", "All fields are required.")
                return

            try:
                new_price = float(new_price)
            except ValueError:
                messagebox.showerror("Error", "Invalid price.")
                return

            execute_query("""
                UPDATE items
                SET name = ?, price = ?, category = ?
                WHERE id = ?
            """, (new_name, new_price, new_category, item_id), commit=True)
            rename_item_column(current_name, new_name)
            messagebox.showinfo("Updated", "Item updated successfully.")
            edit_win.destroy()
            load_items()

        tk.Button(edit_win, text="Save Changes", command=save_changes).pack(pady=10)

    def logout(win):
        admin_win.destroy()
        root.deiconify()

    button_frame = tk.Frame(admin_win)
    button_frame.pack(pady=10)

    tk.Button(button_frame, text="Add Item", command=add_item, width=12).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Edit Item", command=edit_item, width=12).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Delete Item", command=delete_item, width=12).pack(side=tk.LEFT, padx=5)
    tk.Button(button_frame, text="Manage Users", command=user_management_window, width=15).pack(side=tk.LEFT, padx=5)

    button_frame.pack(pady=10)
    logout_button = tk.Button(admin_win, text="Logout", highlightbackground="red", bg="red", fg="black",
                              font=("Arial", 12, "bold"), width=12,
                              command=lambda: logout(admin_win))
    logout_button.pack(pady=10)


def user_management_window():
    user_win = tk.Toplevel()
    user_win.title("Manage Users")
    user_win.geometry("500x400")

    # Treeview
    tree = ttk.Treeview(user_win, columns=("ID", "Username", "Role"), show="headings")
    tree.heading("ID", text="ID")
    tree.heading("Username", text="Username")
    tree.heading("Role", text="Role")
    tree.column("ID", width=50)
    tree.column("Username", width=200)
    tree.column("Role", width=100)
    tree.pack(pady=10, fill=tk.BOTH, expand=True)

    def load_users():
        tree.delete(*tree.get_children())
        for row in execute_query("SELECT id, username, role FROM users ", fetch=True):
            tree.insert("", tk.END, values=row)

    def add_user():
        def save():
            uname, pwd, role = entry_user.get(), entry_pass.get(), var_role.get()
            if not uname or not pwd:
                messagebox.showwarning("Input Error", "Username and Password required.")
                return
            try:
                execute_query("INSERT INTO users (username, password, role) VALUES (?, ?, ?)",
                              params=(uname, pwd, role), commit=True)
                messagebox.showinfo("Success", "User added.")
                load_users()
                win.destroy()
            except sqlite3.IntegrityError:
                messagebox.showerror("Error", "Username already exists.")

        win = tk.Toplevel(user_win)
        win.title("Add User")

        tk.Label(win, text="Username").grid(row=0, column=0)
        tk.Label(win, text="Password").grid(row=1, column=0)
        tk.Label(win, text="Role").grid(row=2, column=0)

        entry_user = tk.Entry(win)
        entry_pass = tk.Entry(win)
        var_role = tk.StringVar(value="user")
        tk.OptionMenu(win, var_role, "user", "admin").grid(row=2, column=1)

        entry_user.grid(row=0, column=1)
        entry_pass.grid(row=1, column=1)

        tk.Button(win, text="Save", command=save).grid(row=3, columnspan=2, pady=10)

    def delete_user():
        selected = tree.selection()
        if not selected:
            return
        user_id = tree.item(selected[0])["values"][0]
        execute_query("DELETE FROM users WHERE id=?", (user_id,), commit=True)
        load_users()
        messagebox.showinfo("Deleted", "User deleted.")

    def edit_user():
        selected = tree.selection()
        if not selected:
            return
        user_id, username, role = tree.item(selected[0])["values"]

        def save():
            new_pass = entry_pass.get()
            new_role = var_role.get()
            if not new_pass:
                messagebox.showwarning("Error", "Password cannot be empty.")
                return
            execute_query("UPDATE users SET password=?, role=? WHERE id=?", params=(new_pass, new_role, user_id),
                          commit=True)
            messagebox.showinfo("Updated", "User updated.")
            load_users()
            win.destroy()

        win = tk.Toplevel(user_win)
        win.title("Edit User")

        tk.Label(win, text=f"Username: {username}").grid(row=0, column=0, columnspan=2)
        tk.Label(win, text="New Password").grid(row=1, column=0)
        entry_pass = tk.Entry(win)
        entry_pass.grid(row=1, column=1)

        tk.Label(win, text="Role").grid(row=2, column=0)
        var_role = tk.StringVar(value=role)
        tk.OptionMenu(win, var_role, "user", "admin").grid(row=2, column=1)

        tk.Button(win, text="Save", command=save).grid(row=3, columnspan=2, pady=10)

    # Button row
    btn_frame = tk.Frame(user_win)
    btn_frame.pack(pady=10)

    tk.Button(btn_frame, text="Add User", command=add_user).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Edit User", command=edit_user).pack(side=tk.LEFT, padx=5)
    tk.Button(btn_frame, text="Delete User", command=delete_user).pack(side=tk.LEFT, padx=5)

    load_users()
