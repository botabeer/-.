import sqlite3
from typing import List, Tuple
import threading
import logging

logger = logging.getLogger("whale-bot.db")

class Database:
    _lock = threading.Lock()

    def __init__(self, db_name: str = "game_bot.db"):
        self.db_name = db_name
        self._create_tables()
        logger.info(f"✅ قاعدة البيانات جاهزة: {db_name}")

    def _create_tables(self):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            # جدول اللاعبين
            c.execute("""
                CREATE TABLE IF NOT EXISTS players (
                    user_id TEXT PRIMARY KEY,
                    name TEXT,
                    points INTEGER DEFAULT 0,
                    last_active TIMESTAMP
                );
            """)
            # سجل الألعاب
            c.execute("""
                CREATE TABLE IF NOT EXISTS game_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    game_name TEXT,
                    result TEXT,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
            conn.commit()

    # --------------------------
    # عمليات اللاعبين
    # --------------------------
    def add_player(self, user_id: str, name: str):
        with self._lock, sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute(
                "INSERT OR IGNORE INTO players (user_id, name) VALUES (?, ?)",
                (user_id, name)
            )
            conn.commit()

    def update_points(self, user_id: str, points: int):
        with self._lock, sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute(
                "UPDATE players SET points = points + ? WHERE user_id = ?",
                (points, user_id)
            )
            conn.commit()

    def get_leaderboard(self) -> List[Tuple[str, int]]:
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute("SELECT name, points FROM players ORDER BY points DESC LIMIT 20")
            return c.fetchall()

    # --------------------------
    # سجل الألعاب
    # --------------------------
    def log_game(self, user_id: str, game_name: str, result: str):
        with sqlite3.connect(self.db_name) as conn:
            c = conn.cursor()
            c.execute(
                "INSERT INTO game_logs (user_id, game_name, result) VALUES (?, ?, ?)",
                (user_id, game_name, result)
            )
            conn.commit()

    # --------------------------
    # وظائف مساعدة للكود الرئيسي
    # --------------------------
    def init_database(self) -> bool:
        try:
            self._create_tables()
            return True
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة قاعدة البيانات: {e}")
            return False

    def get_connection(self):
        try:
            return sqlite3.connect(self.db_name)
        except Exception as e:
            logger.error(f"❌ فشل في الحصول على الاتصال: {e}")
            return None

    def close_connection(self):
        # SQLite connections تغلق تلقائيًا عند الخروج من with
        logger.info("🛑 إغلاق قاعدة البيانات (إذا كان هناك اتصال مفتوح)")

# --------------------------
# إنشاء كائن جاهز للاستخدام
# --------------------------
db_manager = Database()
