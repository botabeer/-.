from database import db_manager
from datetime import datetime

class GameManager:
    """إدارة الألعاب وتسجيل النتائج"""

    def __init__(self):
        self.db = db_manager

    def log_game(self, user_id: str, game_name: str, result: str):
        self.db.log_game(user_id, game_name, result)

    def get_leaderboard(self):
        return self.db.get_leaderboard()
