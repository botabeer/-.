# ============================================
# init_db.py - إنشاء قاعدة البيانات
# ============================================

"""
إنشاء قاعدة بيانات بوت الحوت
==============================
يقوم بإنشاء الجداول والفهارس المطلوبة
"""

import sqlite3
import os
from datetime import datetime


def init_database(db_path='whale_bot.db'):
    """
    إنشاء قاعدة البيانات وجداولها
    
    Args:
        db_path: مسار قاعدة البيانات
    """
    print(f"Creating database at {db_path}...")
    
    # الاتصال بقاعدة البيانات
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # جدول اللاعبين
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                user_id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                points INTEGER DEFAULT 0,
                games_played INTEGER DEFAULT 0,
                games_won INTEGER DEFAULT 0,
                last_active TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # جدول سجل الألعاب
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS game_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                game_type TEXT NOT NULL,
                points_earned INTEGER DEFAULT 0,
                result TEXT,
                played_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES players(user_id)
            )
        ''')
        
        # جدول الجلسات النشطة
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS active_sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                game_type TEXT,
                game_state TEXT,
                started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES players(user_id)
            )
        ''')
        
        # جدول الإحصائيات اليومية
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE NOT NULL,
                total_games INTEGER DEFAULT 0,
                total_players INTEGER DEFAULT 0,
                most_played_game TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(date)
            )
        ''')
        
        # إنشاء الفهارس لتحسين الأداء
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_players_points 
            ON players(points DESC)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_players_last_active 
            ON players(last_active DESC)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_game_history_user 
            ON game_history(user_id, played_at DESC)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_game_history_type 
            ON game_history(game_type, played_at DESC)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_sessions_user 
            ON active_sessions(user_id)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_sessions_activity 
            ON active_sessions(last_activity DESC)
        ''')
        
        # حفظ التغييرات
        conn.commit()
        print("✓ Database created successfully!")
        print("✓ Tables: players, game_history, active_sessions, daily_stats")
        print("✓ Indexes created for optimal performance")
        
    except sqlite3.Error as e:
        print(f"✗ Database error: {e}")
        conn.rollback()
        raise
        
    finally:
        conn.close()


def add_test_data(db_path='whale_bot.db'):
    """
    إضافة بيانات تجريبية للاختبار
    
    Args:
        db_path: مسار قاعدة البيانات
    """
    print("\nAdding test data...")
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # إضافة لاعبين تجريبيين
        test_players = [
            ('U001', 'محمد', 150, 20, 15),
            ('U002', 'أحمد', 120, 18, 10),
            ('U003', 'فاطمة', 100, 15, 8),
            ('U004', 'سارة', 80, 12, 5),
            ('U005', 'علي', 60, 10, 3)
        ]
        
        cursor.executemany('''
            INSERT OR IGNORE INTO players 
            (user_id, name, points, games_played, games_won)
            VALUES (?, ?, ?, ?, ?)
        ''', test_players)
        
        conn.commit()
        print(f"✓ Added {len(test_players)} test players")
        
    except sqlite3.Error as e:
        print(f"✗ Error adding test data: {e}")
        conn.rollback()
        
    finally:
        conn.close()


def cleanup_old_sessions(db_path='whale_bot.db', hours=24):
    """
    تنظيف الجلسات القديمة
    
    Args:
        db_path: مسار قاعدة البيانات
        hours: عدد الساعات للاعتبار قديم
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            DELETE FROM active_sessions
            WHERE datetime(last_activity) < datetime('now', '-' || ? || ' hours')
        ''', (hours,))
        
        deleted = cursor.rowcount
        conn.commit()
        
        if deleted > 0:
            print(f"✓ Cleaned up {deleted} old sessions")
            
    except sqlite3.Error as e:
        print(f"✗ Error cleaning sessions: {e}")
        
    finally:
        conn.close()


def verify_database(db_path='whale_bot.db'):
    """
    التحقق من سلامة قاعدة البيانات
    
    Args:
        db_path: مسار قاعدة البيانات
        
    Returns:
        True إذا كانت سليمة
    """
    if not os.path.exists(db_path):
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # التحقق من وجود الجداول المطلوبة
        cursor.execute('''
            SELECT name FROM sqlite_master 
            WHERE type='table' AND name IN ('players', 'game_history', 'active_sessions', 'daily_stats')
        ''')
        
        tables = cursor.fetchall()
        required_tables = {'players', 'game_history', 'active_sessions', 'daily_stats'}
        existing_tables = {table[0] for table in tables}
        
        if required_tables == existing_tables:
            print("✓ Database integrity verified")
            return True
        else:
            missing = required_tables - existing_tables
            print(f"✗ Missing tables: {missing}")
            return False
            
    except sqlite3.Error as e:
        print(f"✗ Database verification error: {e}")
        return False
        
    finally:
        conn.close()


if __name__ == '__main__':
    """تشغيل مباشر لإنشاء قاعدة البيانات"""
    
    import sys
    
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'whale_bot.db'
    
    print("=" * 50)
    print("Whale Bot Database Initialization")
    print("=" * 50)
    
    # إنشاء قاعدة البيانات
    init_database(db_path)
    
    # التحقق من السلامة
    if verify_database(db_path):
        print("\n✓ Database is ready to use!")
        
        # سؤال عن إضافة بيانات تجريبية
        response = input("\nAdd test data? (y/n): ")
        if response.lower() == 'y':
            add_test_data(db_path)
    else:
        print("\n✗ Database verification failed!")
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("Initialization completed successfully!")
    print("=" * 50)
