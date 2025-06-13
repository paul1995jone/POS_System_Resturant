# main.py

from db.database import init_db
from ui.login_page import open_login_window

if __name__ == "__main__":
    init_db()
    open_login_window()