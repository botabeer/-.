from datetime import datetime, timedelta
‏from typing import Optional, Dict, List
‏import logging

‏logger = logging.getLogger("whale-bot")

‏class UserManager:
    """مدير المستخدمين"""
    
‏    @staticmethod
‏    def update_activity(user_id: str, display_name: str) -> bool:
        """تحديث آخر نشاط للمستخدم"""
‏        from database import db_manager, DatabaseException
‏        from cache import stats_cache
‏        from utils import safe_text
        
‏        try:
‏            now = datetime.now().isoformat()
‏            safe_name = safe_text(display_name, 100)
            
‏            result = db_manager.execute_query(
‏                'SELECT user_id FROM players WHERE user_id = ?',
‏                (user_id,)
            )
            
‏            if result:
‏                db_manager.execute_update(
‏                    'UPDATE players SET last_active = ?, display_name = ? WHERE user_id = ?',
‏                    (now, safe_name, user_id)
                )
‏            else:
‏                db_manager.execute_update(
‏                    'INSERT INTO players (user_id, display_name, last_active) VALUES (?, ?, ?)',
‏                    (user_id, safe_name, now)
                )
            
‏            stats_cache.delete(user_id)
‏            return True
‏        except DatabaseException as e:
‏            logger.error(f"خطأ في تحديث النشاط: {e}")
‏            return False
    
‏    @staticmethod
‏    def update_points(user_id: str, display_name: str, points: int, 
‏                     won: bool = False, game_type: str = '') -> bool:
        """تحديث نقاط اللاعب"""
‏        from database import db_manager, DatabaseException
‏        from cache import stats_cache, leaderboard_cache
‏        from config import NO_POINTS_GAMES
‏        from utils import safe_text
        
‏        if game_type in NO_POINTS_GAMES:
‏            points = 0
        
‏        try:
‏            now = datetime.now().isoformat()
‏            safe_name = safe_text(display_name, 100)
            
‏            result = db_manager.execute_query(
‏                'SELECT total_points, games_played, wins FROM players WHERE user_id = ?',
‏                (user_id,)
            )
            
‏            if result:
‏                user = result[0]
‏                new_points = max(0, user['total_points'] + points)
‏                new_games = user['games_played'] + 1
‏                new_wins = user['wins'] + (1 if won else 0)
                
‏                db_manager.execute_update('''
‏                    UPDATE players 
‏                    SET total_points = ?, games_played = ?, wins = ?, 
‏                        last_active = ?, display_name = ? 
‏                    WHERE user_id = ?
‏                ''', (new_points, new_games, new_wins, now, safe_name, user_id))
‏            else:
‏                db_manager.execute_update('''
‏                    INSERT INTO players 
‏                    (user_id, display_name, total_points, games_played, wins, last_active) 
‏                    VALUES (?, ?, ?, 1, ?, ?)
‏                ''', (user_id, safe_name, max(0, points), 1 if won else 0, now))
            
‏            if game_type and points != 0:
‏                db_manager.execute_update(
‏                    'INSERT INTO game_history (user_id, game_type, points, won) VALUES (?, ?, ?, ?)',
‏                    (user_id, game_type, points, 1 if won else 0)
                )
            
‏            stats_cache.delete(user_id)
‏            leaderboard_cache.clear()
‏            return True
‏        except DatabaseException as e:
‏            logger.error(f"خطأ في تحديث النقاط: {e}")
‏            return False
    
‏    @staticmethod
‏    def get_stats(user_id: str) -> Optional[Dict]:
        """جلب إحصائيات اللاعب"""
‏        from database import db_manager, DatabaseException
‏        from cache import stats_cache
        
‏        cached = stats_cache.get(user_id)
‏        if cached:
‏            return cached
        
‏        try:
‏            result = db_manager.execute_query(
‏                'SELECT * FROM players WHERE user_id = ?',
‏                (user_id,)
            )
            
‏            if result:
‏                stats = dict(result[0])
‏                stats_cache.set(user_id, stats)
‏                return stats
‏            return None
‏        except DatabaseException as e:
‏            logger.error(f"خطأ في جلب الإحصائيات: {e}")
‏            return None
    
‏    @staticmethod
‏    def get_leaderboard(limit: int = 10) -> List[Dict]:
        """جلب لوحة الصدارة"""
‏        from database import db_manager, DatabaseException
‏        from cache import leaderboard_cache
        
‏        cache_key = f"leaderboard_{limit}"
‏        cached = leaderboard_cache.get(cache_key)
‏        if cached:
‏            return cached
        
‏        try:
‏            result = db_manager.execute_query('''
‏                SELECT display_name, total_points, games_played, wins 
‏                FROM players 
‏                WHERE total_points > 0
‏                ORDER BY total_points DESC, wins DESC 
‏                LIMIT ?
‏            ''', (limit,))
            
‏            leaders = [dict(row) for row in result]
‏            leaderboard_cache.set(cache_key, leaders)
‏            return leaders
‏        except DatabaseException as e:
‏            logger.error(f"خطأ في جلب الصدارة: {e}")
‏            return []
    
‏    @staticmethod
‏    def cleanup_inactive(days: int = 45) -> int:
        """حذف المستخدمين غير النشطين"""
‏        from database import db_manager, DatabaseException
‏        from cache import stats_cache, leaderboard_cache
        
‏        try:
‏            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
‏            result = db_manager.execute_query(
‏                'SELECT COUNT(*) as count FROM players WHERE last_active < ?',
‏                (cutoff_date,)
            )
‏            count = result[0]['count'] if result else 0
            
‏            if count > 0:
‏                db_manager.execute_update(
‏                    'DELETE FROM players WHERE last_active < ?',
‏                    (cutoff_date,)
                )
                
‏                logger.info(f"تم حذف {count} مستخدم غير نشط")
‏                stats_cache.clear()
‏                leaderboard_cache.clear()
            
‏            return count
‏        except DatabaseException as e:
‏            logger.error(f"خطأ في تنظيف المستخدمين: {e}")
‏            return 0
