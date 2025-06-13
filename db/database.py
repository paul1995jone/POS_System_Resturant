import sqlite3, os, csv


def init_db():
    # ✅ DO NOT delete the database file
    # if os.path.exists("restaurant.db"):
    #     os.remove("restaurant.db")

    conn = sqlite3.connect("restaurant.db")
    cursor = conn.cursor()

    # ✅ Create tables only if they don't exist
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        role TEXT NOT NULL CHECK(role IN ('admin', 'user'))
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        is_available INTEGER DEFAULT 1,
        category TEXT DEFAULT 'veg'
    )
    """)

    # ✅ Insert default admin user only if not already exists
    cursor.execute("""
    SELECT COUNT(*) FROM users WHERE username = 'admin'
    """)
    if cursor.fetchone()[0] == 0:
        cursor.execute("""
        INSERT INTO users (username, password, role) 
        VALUES ('admin', 'admin123', 'admin')
        """)

    conn.commit()
    conn.close()


def initialize_item_history_csv():
    file_path = "Item_history.csv"

    if os.path.exists(file_path):
        user_input = input(f"⚠️ '{file_path}' already exists. Do you want to overwrite it? (yes/no): ").strip().lower()
        if user_input != "yes":
            print("ℹ️ Keeping the existing file. No changes made.")
            return

    with open(file_path, mode='w', newline='') as csv_file:
        writer = csv.writer(csv_file)
        writer.writerow(["Serial No", "Date", "Occasion", "Weather"])
    print(f"✅ '{file_path}' has been created/reset with default headers.")


if __name__ == "__main__":
    init_db()
    print("✅ Database initialized (tables ensured, admin added if missing).")
    initialize_item_history_csv()
