from database import db_manager
from utils import safe_text, normalize_text
from cache import names_cache
from datetime import datetime

class UserManager:
    """إدارة معلومات المستخدمين"""

    def __init__(self):
        self.db = db_manager

    def add_user(self, user_id: str, display_name: str):
        display_name = safe_text(display_name, 50)
        self.db.add_player(user_id, display_name)
        names_cache.set(user_id, display_name)

    def get_display_name(self, user_id: str) -> str:
        cached = names_cache.get(user_id)
        if cached:
            return cached

        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM players WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        if row:
            names_cache.set(user_id, row["name"])
            return row["name"]
        return f"لاعب {user_id[-4:]}"

    def add_points(self, user_id: str, points: int):
        self.db.update_points(user_id, points)
