"""وظائف قاعدة البيانات"""
import sqlite3
from datetime import datetime
import logging
from .settings import DB_NAME

logger = logging.getLogger(__name__)

def get_conn():
    conn = sqlite3.connect(DB_NAME, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS users
                     (user_id TEXT PRIMARY KEY, display_name TEXT,
                      total_points INTEGER DEFAULT 0, games_played INTEGER DEFAULT 0,
                      wins INTEGER DEFAULT 0, last_played TEXT,
                      registered_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
        c.execute('''CREATE TABLE IF NOT EXISTS game_history
                     (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT,
                      game_type TEXT, points INTEGER, won INTEGER,
                      played_at TEXT DEFAULT CURRENT_TIMESTAMP)''')
        c.execute('CREATE INDEX IF NOT EXISTS idx_points ON users(total_points DESC)')
        conn.commit()
        conn.close()
        logger.info("✅ قاعدة البيانات جاهزة")
        return True
    except Exception as e:
        logger.error(f"❌ خطأ DB: {e}")
        return False

def update_points(user_id, name, points, won=False, game_type=""):
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = c.fetchone()
        
        if user:
            c.execute('''UPDATE users SET total_points = ?, games_played = ?, 
                         wins = ?, last_played = ?, display_name = ? 
                         WHERE user_id = ?''',
                      (user['total_points'] + points, user['games_played'] + 1,
                       user['wins'] + (1 if won else 0), datetime.now().isoformat(),
                       name, user_id))
        else:
            c.execute('''INSERT INTO users VALUES (?, ?, ?, ?, ?, ?, ?)''',
                      (user_id, name, points, 1, 1 if won else 0, 
                       datetime.now().isoformat(), datetime.now().isoformat()))
        
        if game_type:
            c.execute('INSERT INTO game_history VALUES (NULL, ?, ?, ?, ?, ?)',
                      (user_id, game_type, points, 1 if won else 0, datetime.now().isoformat()))
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"❌ خطأ تحديث: {e}")
        return False

def get_stats(user_id):
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = c.fetchone()
        conn.close()
        return user
    except:
        return None

def get_leaderboard(limit=10):
    try:
        conn = get_conn()
        c = conn.cursor()
        c.execute('SELECT * FROM users ORDER BY total_points DESC LIMIT ?', (limit,))
        leaders = c.fetchall()
        conn.close()
        return leaders
    except:
        return []
