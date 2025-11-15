"""
Database Configuration and Functions
Handles all database operations for the game bot
"""

import sqlite3
import os
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Database file path
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'game_bot.db')

def get_connection():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database and create tables"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Create players table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                user_id TEXT PRIMARY KEY,
                display_name TEXT NOT NULL,
                total_points INTEGER DEFAULT 0,
                games_played INTEGER DEFAULT 0,
                wins INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Create game_history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                game_type TEXT NOT NULL,
                points INTEGER DEFAULT 0,
                won BOOLEAN DEFAULT 0,
                played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES players(user_id)
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_players_points 
            ON players(total_points DESC)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_game_history_user 
            ON game_history(user_id, played_at)
        ''')
        
        conn.commit()
        conn.close()
        logger.info("✅ Database initialized successfully")
        
    except Exception as e:
        logger.error(f"❌ Error initializing database: {e}")

def update_points(user_id, display_name, points, won=False, game_type='unknown'):
    """Update player points and statistics"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Check if player exists
        cursor.execute('SELECT * FROM players WHERE user_id = ?', (user_id,))
        player = cursor.fetchone()
        
        if player:
            # Update existing player
            cursor.execute('''
                UPDATE players 
                SET display_name = ?,
                    total_points = total_points + ?,
                    games_played = games_played + 1,
                    wins = wins + ?,
                    last_active = ?
                WHERE user_id = ?
            ''', (display_name, points, 1 if won else 0, datetime.now(), user_id))
        else:
            # Insert new player
            cursor.execute('''
                INSERT INTO players (user_id, display_name, total_points, games_played, wins)
                VALUES (?, ?, ?, 1, ?)
            ''', (user_id, display_name, points, 1 if won else 0))
        
        # Add to game history
        cursor.execute('''
            INSERT INTO game_history (user_id, game_type, points, won)
            VALUES (?, ?, ?, ?)
        ''', (user_id, game_type, points, won))
        
        conn.commit()
        conn.close()
        logger.info(f"✅ Updated points for {display_name}: +{points} points")
        
    except Exception as e:
        logger.error(f"❌ Error updating points: {e}")

def get_stats(user_id):
    """Get player statistics"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                user_id,
                display_name,
                total_points,
                games_played,
                wins,
                created_at,
                last_active
            FROM players 
            WHERE user_id = ?
        ''', (user_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'user_id': row['user_id'],
                'display_name': row['display_name'],
                'total_points': row['total_points'],
                'games_played': row['games_played'],
                'wins': row['wins'],
                'created_at': row['created_at'],
                'last_active': row['last_active']
            }
        return None
        
    except Exception as e:
        logger.error(f"❌ Error getting stats: {e}")
        return None

def get_leaderboard(limit=10):
    """Get top players leaderboard"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                user_id,
                display_name,
                total_points,
                games_played,
                wins
            FROM players 
            ORDER BY total_points DESC, wins DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        leaderboard = []
        for row in rows:
            leaderboard.append({
                'user_id': row['user_id'],
                'display_name': row['display_name'],
                'total_points': row['total_points'],
                'games_played': row['games_played'],
                'wins': row['wins']
            })
        
        return leaderboard
        
    except Exception as e:
        logger.error(f"❌ Error getting leaderboard: {e}")
        return []

def get_game_history(user_id, limit=20):
    """Get player's game history"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                id,
                game_type,
                points,
                won,
                played_at
            FROM game_history 
            WHERE user_id = ?
            ORDER BY played_at DESC
            LIMIT ?
        ''', (user_id, limit))
        
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            history.append({
                'id': row['id'],
                'game_type': row['game_type'],
                'points': row['points'],
                'won': bool(row['won']),
                'played_at': row['played_at']
            })
        
        return history
        
    except Exception as e:
        logger.error(f"❌ Error getting game history: {e}")
        return []

def get_game_stats_summary():
    """Get overall game statistics"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Total players
        cursor.execute('SELECT COUNT(*) as count FROM players')
        total_players = cursor.fetchone()['count']
        
        # Total games played
        cursor.execute('SELECT COUNT(*) as count FROM game_history')
        total_games = cursor.fetchone()['count']
        
        # Most popular game
        cursor.execute('''
            SELECT game_type, COUNT(*) as count 
            FROM game_history 
            GROUP BY game_type 
            ORDER BY count DESC 
            LIMIT 1
        ''')
        popular_game = cursor.fetchone()
        
        # Top player
        cursor.execute('''
            SELECT display_name, total_points 
            FROM players 
            ORDER BY total_points DESC 
            LIMIT 1
        ''')
        top_player = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_players': total_players,
            'total_games': total_games,
            'popular_game': popular_game['game_type'] if popular_game else None,
            'popular_game_count': popular_game['count'] if popular_game else 0,
            'top_player': top_player['display_name'] if top_player else None,
            'top_player_points': top_player['total_points'] if top_player else 0
        }
        
    except Exception as e:
        logger.error(f"❌ Error getting game stats: {e}")
        return None

def reset_player_stats(user_id):
    """Reset player statistics (admin function)"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE players 
            SET total_points = 0,
                games_played = 0,
                wins = 0
            WHERE user_id = ?
        ''', (user_id,))
        
        cursor.execute('DELETE FROM game_history WHERE user_id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        logger.info(f"✅ Reset stats for user {user_id}")
        return True
        
    except Exception as e:
        logger.error(f"❌ Error resetting player stats: {e}")
        return False

def cleanup_old_data(days=90):
    """Clean up old game history data"""
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM game_history 
            WHERE played_at < datetime('now', '-' || ? || ' days')
        ''', (days,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        logger.info(f"🗑️ Cleaned up {deleted_count} old game records")
        return deleted_count
        
    except Exception as e:
        logger.error(f"❌ Error cleaning up data: {e}")
        return 0
