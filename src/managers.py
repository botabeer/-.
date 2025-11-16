# src/managers.py
from database import Database

class UserManager:
    def __init__(self, db: Database):
        self.db = db
    # وظائف إدارة اللاعبين

class GameManager:
    def __init__(self, db: Database):
        self.db = db
    # وظائف إدارة الألعاب

def cleanup_manager():
    # تنظيف الكاش أو أي مهام مؤقتة
    pass
