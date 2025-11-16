# managers.py
from database import Database

class UserManager:
    def __init__(self, db: Database):
        self.db = db
    # هنا كل وظائف إدارة اللاعبين

class GameManager:
    def __init__(self, db: Database):
        self.db = db
    # هنا كل وظائف إدارة الألعاب

def cleanup_manager():
    # هنا وظيفة تنظيف أو إعادة ضبط أي شيء مؤقت
    pass
