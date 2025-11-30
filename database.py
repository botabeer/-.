"""
Whale Bot - Database Manager
"""

import sqlite3
import threading
from datetime import datetime
from constants import DB_PATH

class Database:
    def __init__(self):
        self.db_path = DB_PATH
        self.lock = threading.Lock()
        self._init_database()
    
    def _get_connection(self):
        """إنشاء اتصال جديد بقاعدة البيانات"""
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _init_database(self):
        """تهيئة قاعدة البيانات"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            # جدول اللاعبين
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS players (
                    user_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    points INTEGER DEFAULT 0,
                    games_played INTEGER DEFAULT 0,
                    games_won INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # الفهارس
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_points ON players(points DESC)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_active ON players(last_active DESC)')
            
            conn.commit()
            conn.close()
    
    def get_player(self, user_id):
        """جلب معلومات اللاعب"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM players WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            conn.close()
            return dict(row) if row else None
    
    def create_player(self, user_id, name):
        """إنشاء لاعب جديد"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                'INSERT OR IGNORE INTO players (user_id, name) VALUES (?, ?)',
                (user_id, name)
            )
            conn.commit()
            conn.close()
    
    def update_player_name(self, user_id, name):
        """تحديث اسم اللاعب"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE players SET name = ?, last_active = ? WHERE user_id = ?',
                (name, datetime.now(), user_id)
            )
            conn.commit()
            conn.close()
    
    def add_points(self, user_id, points):
        """إضافة نقاط للاعب"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE players SET points = points + ?, last_active = ? WHERE user_id = ?',
                (points, datetime.now(), user_id)
            )
            conn.commit()
            conn.close()
    
    def update_game_stats(self, user_id, won=False):
        """تحديث إحصائيات الألعاب"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            
            if won:
                cursor.execute(
                    '''UPDATE players 
                       SET games_played = games_played + 1, 
                           games_won = games_won + 1, 
                           last_active = ? 
                       WHERE user_id = ?''',
                    (datetime.now(), user_id)
                )
            else:
                cursor.execute(
                    '''UPDATE players 
                       SET games_played = games_played + 1, 
                           last_active = ? 
                       WHERE user_id = ?''',
                    (datetime.now(), user_id)
                )
            
            conn.commit()
            conn.close()
    
    def get_leaderboard(self, limit=10):
        """جلب لوحة الصدارة"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                '''SELECT user_id, name, points 
                   FROM players 
                   WHERE points > 0 
                   ORDER BY points DESC 
                   LIMIT ?''',
                (limit,)
            )
            rows = cursor.fetchall()
            conn.close()
            return [dict(r) for r in rows]
    
    def get_player_rank(self, user_id):
        """جلب ترتيب اللاعب"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute(
                '''SELECT COUNT(*) + 1 
                   FROM players 
                   WHERE points > (SELECT points FROM players WHERE user_id = ?)''',
                (user_id,)
            )
            rank = cursor.fetchone()[0]
            conn.close()
            return rank
    
    def get_total_players(self):
        """عدد اللاعبين الكلي"""
        with self.lock:
            conn = self._get_connection()
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM players')
            count = cursor.fetchone()[0]
            conn.close()
            return count
