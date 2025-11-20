"""
Database Manager
================
Simplified database operations
"""

import sqlite3
from contextlib import contextmanager
from config import DB_PATH

class Database:
    def __init__(self):
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema"""
        with self.connection() as conn:
            conn.executescript('''
                CREATE TABLE IF NOT EXISTS players (
                    user_id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    points INTEGER DEFAULT 0,
                    games_played INTEGER DEFAULT 0,
                    games_won INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
                
                CREATE INDEX IF NOT EXISTS idx_points 
                ON players(points DESC);
                
                CREATE INDEX IF NOT EXISTS idx_active 
                ON players(last_active DESC);
            ''')
    
    @contextmanager
    def connection(self):
        """Get database connection"""
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()
    
    def get_player(self, user_id):
        """Get player by ID"""
        with self.connection() as conn:
            result = conn.execute(
                'SELECT * FROM players WHERE user_id = ?', 
                (user_id,)
            ).fetchone()
            return dict(result) if result else None
    
    def create_player(self, user_id, name):
        """Create new player"""
        with self.connection() as conn:
            conn.execute(
                'INSERT OR IGNORE INTO players (user_id, name) VALUES (?, ?)',
                (user_id, name)
            )
            conn.execute(
                'UPDATE players SET last_active = CURRENT_TIMESTAMP WHERE user_id = ?',
                (user_id,)
            )
        return self.get_player(user_id)
    
    def update_points(self, user_id, points):
        """Update player points"""
        with self.connection() as conn:
            conn.execute(
                'UPDATE players SET points = points + ? WHERE user_id = ?',
                (points, user_id)
            )
    
    def update_stats(self, user_id, won=False):
        """Update game statistics"""
        with self.connection() as conn:
            if won:
                conn.execute(
                    'UPDATE players SET games_played = games_played + 1, games_won = games_won + 1 WHERE user_id = ?',
                    (user_id,)
                )
            else:
                conn.execute(
                    'UPDATE players SET games_played = games_played + 1 WHERE user_id = ?',
                    (user_id,)
                )
    
    def get_leaderboard(self, limit=10):
        """Get top players"""
        with self.connection() as conn:
            results = conn.execute(
                'SELECT name, points FROM players WHERE points > 0 ORDER BY points DESC LIMIT ?',
                (limit,)
            ).fetchall()
            return [dict(r) for r in results]

db = Database()
