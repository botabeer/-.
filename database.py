# ============================================
# database.py - مدير قواعد البيانات الموحد
# ============================================

import sqlite3
import os
from contextlib import contextmanager
from rules import DB_NAME, POSTGRES_CONFIG, REDIS_CONFIG, DB_SCHEMA
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """مدير موحد لقواعد البيانات (SQLite/PostgreSQL) مع Redis Cache"""
    
    def __init__(self):
        self.db_type = 'postgres' if POSTGRES_CONFIG['enabled'] else 'sqlite'
        self.redis_client = None
        self._init_redis()
        self._init_database()
    
    def _init_redis(self):
        """تهيئة Redis للتخزين المؤقت"""
        if not REDIS_CONFIG['enabled']:
            return
        try:
            import redis
            self.redis_client = redis.Redis(
                host=REDIS_CONFIG['host'], port=REDIS_CONFIG['port'],
                db=REDIS_CONFIG['db'], password=REDIS_CONFIG['password'],
                decode_responses=REDIS_CONFIG['decode_responses']
            )
            self.redis_client.ping()
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}")
            self.redis_client = None
    
    def _init_database(self):
        """تهيئة قاعدة البيانات"""
        if self.db_type == 'postgres':
            self._init_postgres()
        else:
            self._init_sqlite()
    
    def _init_sqlite(self):
        """تهيئة SQLite"""
        conn = sqlite3.connect(DB_NAME)
        conn.executescript(DB_SCHEMA)
        conn.commit()
        conn.close()
        logger.info("SQLite initialized")
    
    def _init_postgres(self):
        """تهيئة PostgreSQL"""
        try:
            import psycopg2
            from psycopg2 import pool
            self.pg_pool = psycopg2.pool.ThreadedConnectionPool(
                1, POSTGRES_CONFIG['pool_size'],
                host=POSTGRES_CONFIG['host'], port=POSTGRES_CONFIG['port'],
                database=POSTGRES_CONFIG['database'], user=POSTGRES_CONFIG['user'],
                password=POSTGRES_CONFIG['password']
            )
            # تحويل schema لـ PostgreSQL
            pg_schema = DB_SCHEMA.replace('AUTOINCREMENT', 'SERIAL')
            with self.get_connection() as conn:
                conn.execute(pg_schema)
            logger.info("PostgreSQL initialized")
        except Exception as e:
            logger.error(f"PostgreSQL init failed: {e}")
            self.db_type = 'sqlite'
            self._init_sqlite()
    
    @contextmanager
    def get_connection(self):
        """الحصول على اتصال بقاعدة البيانات"""
        if self.db_type == 'postgres':
            conn = self.pg_pool.getconn()
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                self.pg_pool.putconn(conn)
        else:
            conn = sqlite3.connect(DB_NAME)
            conn.row_factory = sqlite3.Row
            try:
                yield conn
                conn.commit()
            except Exception as e:
                conn.rollback()
                raise e
            finally:
                conn.close()
    
    def cache_get(self, key):
        """الحصول من Cache"""
        if not self.redis_client:
            return None
        try:
            return self.redis_client.get(key)
        except:
            return None
    
    def cache_set(self, key, value, ttl=None):
        """حفظ في Cache"""
        if not self.redis_client:
            return
        try:
            ttl = ttl or REDIS_CONFIG['cache_ttl']
            self.redis_client.setex(key, ttl, value)
        except:
            pass
    
    def cache_delete(self, key):
        """حذف من Cache"""
        if self.redis_client:
            try:
                self.redis_client.delete(key)
            except:
                pass
    
    def get_player(self, user_id):
        """الحصول على لاعب مع Cache"""
        cache_key = f"player:{user_id}"
        cached = self.cache_get(cache_key)
        if cached:
            return eval(cached)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM players WHERE user_id = ?', (user_id,))
            result = cursor.fetchone()
            if result:
                player = dict(result)
                self.cache_set(cache_key, str(player))
                return player
        return None
    
    def create_player(self, user_id, name):
        """إنشاء لاعب جديد"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('INSERT INTO players (user_id, name) VALUES (?, ?)', (user_id, name))
            self.cache_delete(f"player:{user_id}")
        return self.get_player(user_id)
    
    def update_points(self, user_id, points):
        """تحديث النقاط"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE players SET points = points + ?, last_active = CURRENT_TIMESTAMP WHERE user_id = ?', (points, user_id))
            self.cache_delete(f"player:{user_id}")
            self.cache_delete("leaderboard")
    
    def get_leaderboard(self, limit=10):
        """الحصول على المتصدرين مع Cache"""
        cached = self.cache_get("leaderboard")
        if cached:
            return eval(cached)
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT name, points, ROW_NUMBER() OVER (ORDER BY points DESC) as rank FROM players WHERE points > 0 ORDER BY points DESC LIMIT ?', (limit,))
            result = [dict(row) for row in cursor.fetchall()]
            self.cache_set("leaderboard", str(result))
            return result
    
    def update_game_stats(self, user_id, won=False):
        """تحديث إحصائيات الألعاب"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            if won:
                cursor.execute('UPDATE players SET games_played = games_played + 1, games_won = games_won + 1 WHERE user_id = ?', (user_id,))
            else:
                cursor.execute('UPDATE players SET games_played = games_played + 1 WHERE user_id = ?', (user_id,))
            self.cache_delete(f"player:{user_id}")

db = DatabaseManager()
