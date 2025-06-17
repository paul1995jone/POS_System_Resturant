import os, csv, sys
from datetime import datetime
import tkinter as tk
import sqlite3
from tkinter import messagebox

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS  # When running from .exe
    except AttributeError:
        base_path = os.path.abspath(".")  # When running normally
    return os.path.join(base_path, relative_path)

def get_occasion_and_weather():
    def on_submit():
        nonlocal occasion_value, weather_value
        occasion_value = occasion_entry.get().strip()
        weather_value = weather_entry.get().strip()
        popup.destroy()

    occasion_value = ""
    weather_value = ""

    popup = tk.Toplevel()
    popup.title("For Future Growth")
    popup.geometry("300x200")
    popup.grab_set()  # Prevent interaction with other windows

    tk.Label(popup, text="Any Occasion Today:", font=("Arial", 11)).pack(pady=(20, 5))
    occasion_entry = tk.Entry(popup, width=30)
    occasion_entry.pack(pady=5)

    tk.Label(popup, text="Today's Weather Condition:", font=("Arial", 11)).pack(pady=(10, 5))
    weather_entry = tk.Entry(popup, width=30)
    weather_entry.pack(pady=5)

    submit_btn = tk.Button(popup, text="Submit", command=on_submit, bg="green", fg="black", font=("Arial", 10, "bold"))
    submit_btn.pack(pady=15)

    popup.wait_window()  # Wait until the window is closed
    return occasion_value, weather_value

CSV_FILE = resource_path("Item_history.csv")
def add_today_entry():
    today = datetime.now().date().isoformat()
    occasion, weather = get_occasion_and_weather()

    # Get current header
    with open(CSV_FILE, 'r') as f:
        reader = csv.reader(f)
        rows = list(reader)
        header = rows[0]
        total_columns = len(header)
        serial_no = len(rows)  # Assuming header is first row

    # Build new row with first 4 values
    new_row = [serial_no, today, occasion, weather]

    # Fill remaining columns with blank
    new_row += [''] * (total_columns - len(new_row))

    with open(CSV_FILE, 'a', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(new_row)


def entry_exists_for_today():
    today = datetime.now().date().isoformat()
    if not os.path.exists(CSV_FILE):
        return False

    with open(CSV_FILE, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row["Date"] == today:
                return True
    return False


def record_daily_history_if_needed():
    if not entry_exists_for_today():
        add_today_entry()


def execute_query(query, params=None, fetch=False, fetchone=False, commit=False, many=False):
    """
    Execute SQL queries (single or many) with optional fetching and committing.

    Args:
        query (str): SQL query with placeholders.
        params: tuple/list for single, or list of tuples for many.
        fetch (bool): Fetch all rows.
        fetchone (bool): Fetch one row.
        commit (bool): Commit transaction.
        many (bool): Use executemany for bulk operations.

    Returns:
        List/tuple of results or None.
    """
    result = None

    try:
        with sqlite3.connect(resource_path("resturant.db")) as conn:
            cursor = conn.cursor()
            if many and params:
                cursor.executemany(query, params)
            elif params:
                cursor.execute(query, params)
            else:
                cursor.execute(query)

            if commit:
                conn.commit()

            if fetch:
                result = cursor.fetchall()
            elif fetchone:
                result = cursor.fetchone()
    except sqlite3.Error as e:
        messagebox.showwarning(f"{e}")
    return result

