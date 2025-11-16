import sqlite3
‏import threading
‏from typing import Optional, List
‏import logging

‏logger = logging.getLogger("whale-bot")

‏class DatabaseException(Exception):
    """خطأ في قاعدة البيانات"""
‏    pass

‏class DatabaseManager:
    """مدير قاعدة البيانات"""
    
‏    def __init__(self, db_name: str):
‏        self.db_name = db_name
‏        self._local = threading.local()
    
‏    def get_connection(self):
        """الحصول على اتصال thread-safe"""
‏        if not hasattr(self._local, 'conn') or self._local.conn is None:
‏            try:
‏                self._local.conn = sqlite3.connect(
‏                    self.db_name,
‏                    check_same_thread=False,
‏                    timeout=10,
‏                    isolation_level='DEFERRED'
                )
‏                self._local.conn.row_factory = sqlite3.Row
‏                self._local.conn.execute('PRAGMA foreign_keys = ON')
‏                self._local.conn.execute('PRAGMA journal_mode = WAL')
‏                self._local.conn.execute('PRAGMA synchronous = NORMAL')
‏            except Exception as e:
‏                logger.error(f"فشل الاتصال بقاعدة البيانات: {e}")
‏                raise DatabaseException(f"Database connection failed: {e}")
        
‏        return self._local.conn
    
‏    def close_connection(self):
        """إغلاق الاتصال"""
‏        if hasattr(self._local, 'conn') and self._local.conn:
‏            self._local.conn.close()
‏            self._local.conn = None
    
‏    def init_database(self) -> bool:
        """تهيئة قاعدة البيانات"""
‏        try:
‏            conn = self.get_connection()
‏            cursor = conn.cursor()
            
‏            cursor.execute('''
‏                CREATE TABLE IF NOT EXISTS players (
‏                    user_id TEXT PRIMARY KEY,
‏                    display_name TEXT NOT NULL,
‏                    total_points INTEGER DEFAULT 0 CHECK(total_points >= 0),
‏                    games_played INTEGER DEFAULT 0 CHECK(games_played >= 0),
‏                    wins INTEGER DEFAULT 0 CHECK(wins >= 0),
‏                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
‏                    last_active TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
‏            cursor.execute('''
‏                CREATE TABLE IF NOT EXISTS game_history (
‏                    id INTEGER PRIMARY KEY AUTOINCREMENT,
‏                    user_id TEXT NOT NULL,
‏                    game_type TEXT NOT NULL,
‏                    points INTEGER DEFAULT 0,
‏                    won INTEGER DEFAULT 0 CHECK(won IN (0, 1)),
‏                    played_at TEXT DEFAULT CURRENT_TIMESTAMP,
‏                    FOREIGN KEY (user_id) REFERENCES players(user_id) ON DELETE CASCADE
                )
            ''')
            
‏            cursor.execute('CREATE INDEX IF NOT EXISTS idx_points ON players(total_points DESC)')
‏            cursor.execute('CREATE INDEX IF NOT EXISTS idx_active ON players(last_active DESC)')
‏            cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_user ON game_history(user_id, played_at DESC)')
            
‏            conn.commit()
‏            logger.info("قاعدة البيانات جاهزة")
‏            return True
‏        except Exception as e:
‏            logger.error(f"خطأ في تهيئة قاعدة البيانات: {e}")
‏            return False
    
‏    def execute_query(self, query: str, params: tuple = ()) -> Optional[List]:
        """تنفيذ استعلام SELECT"""
‏        try:
‏            conn = self.get_connection()
‏            cursor = conn.cursor()
‏            cursor.execute(query, params)
‏            return cursor.fetchall()
‏        except Exception as e:
‏            logger.error(f"خطأ في تنفيذ الاستعلام: {e}")
‏            raise DatabaseException(f"Query execution failed: {e}")
    
‏    def execute_update(self, query: str, params: tuple = ()) -> bool:
        """تنفيذ استعلام UPDATE/INSERT/DELETE"""
‏        try:
‏            conn = self.get_connection()
‏            cursor = conn.cursor()
‏            cursor.execute(query, params)
‏            conn.commit()
‏            return True
‏        except Exception as e:
‏            logger.error(f"خطأ في تنفيذ التحديث: {e}")
‏            conn.rollback()
‏            raise DatabaseException(f"Update execution failed: {e}")

‏from config import config
‏db_manager = DatabaseManager(config.db_name)
