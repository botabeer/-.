import sqlite3
from datetime import datetime
import os

class Database:
    def __init__(self, db_path='whale_bot.db'):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def init_db(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
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
            
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS game_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT NOT NULL,
                    game_type TEXT NOT NULL,
                    points_earned INTEGER DEFAULT 0,
                    rounds_completed INTEGER DEFAULT 0,
                    won BOOLEAN DEFAULT 0,
                    played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES players(user_id)
                )
            ''')
            
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_points ON players(points DESC)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_active ON players(last_active DESC)')
            cursor.execute('CREATE INDEX IF NOT EXISTS idx_history_user ON game_history(user_id, played_at DESC)')
            
            conn.commit()
    
    def get_player(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM players WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if row:
                return {
                    'user_id': row[0],
                    'name': row[1],
                    'points': row[2],
                    'games_played': row[3],
                    'games_won': row[4],
                    'created_at': row[5],
                    'last_active': row[6]
                }
            return None
    
    def create_player(self, user_id, name):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO players (user_id, name) VALUES (?, ?)',
                (user_id, name)
            )
            conn.commit()
    
    def update_name(self, user_id, name):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE players SET name = ?, last_active = ? WHERE user_id = ?',
                (name, datetime.now(), user_id)
            )
            conn.commit()
    
    def update_points(self, user_id, points):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE players SET points = points + ?, last_active = ? WHERE user_id = ?',
                (points, datetime.now(), user_id)
            )
            conn.commit()
    
    def update_stats(self, user_id, won=False):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if won:
                cursor.execute(
                    'UPDATE players SET games_played = games_played + 1, games_won = games_won + 1, last_active = ? WHERE user_id = ?',
                    (datetime.now(), user_id)
                )
            else:
                cursor.execute(
                    'UPDATE players SET games_played = games_played + 1, last_active = ? WHERE user_id = ?',
                    (datetime.now(), user_id)
                )
            conn.commit()
    
    def get_leaderboard(self, limit=10):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT user_id, name, points FROM players ORDER BY points DESC LIMIT ?',
                (limit,)
            )
            rows = cursor.fetchall()
            return [{'user_id': r[0], 'name': r[1], 'points': r[2]} for r in rows]
    
    def get_player_rank(self, user_id):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT COUNT(*) + 1 FROM players WHERE points > (SELECT points FROM players WHERE user_id = ?)',
                (user_id,)
            )
            return cursor.fetchone()[0]
    
    def save_game_history(self, user_id, game_type, points_earned, rounds_completed, won):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO game_history (user_id, game_type, points_earned, rounds_completed, won) VALUES (?, ?, ?, ?, ?)',
                (user_id, game_type, points_earned, rounds_completed, int(won))
            )
            conn.commit()
    
    def get_player_history(self, user_id, limit=10):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT game_type, points_earned, rounds_completed, won, played_at FROM game_history WHERE user_id = ? ORDER BY played_at DESC LIMIT ?',
                (user_id, limit)
            )
            rows = cursor.fetchall()
            return [{'game_type': r[0], 'points_earned': r[1], 'rounds_completed': r[2], 'won': bool(r[3]), 'played_at': r[4]} for r in rows]
