"""التنظيف التلقائي"""
‏import threading
‏import time
‏from datetime import datetime, timedelta
‏import logging

‏logger = logging.getLogger("whale-bot")

‏class CleanupManager:
    """مدير التنظيف التلقائي"""
    
‏    def __init__(self):
‏        self.last_cleanup = None
‏        self.running = True
    
‏    def cleanup_task(self, active_games, games_lock, config):
        """مهمة التنظيف التلقائي"""
‏        from cache import names_cache, stats_cache
‏        from managers.user_manager import UserManager
‏        from managers.game_manager import GameManager
        
‏        while self.running:
‏            try:
‏                time.sleep(config.cleanup_interval_seconds)
‏                now = datetime.now()
                
                # تنظيف الألعاب القديمة
‏                GameManager.cleanup_old_games(active_games, games_lock, config.game_timeout_minutes)
                
                # تنظيف الذاكرة المؤقتة
‏                names_expired = names_cache.cleanup()
‏                stats_expired = stats_cache.cleanup()
‏                if names_expired > 0 or stats_expired > 0:
‏                    logger.info(f"🧹 تنظيف الذاكرة: {names_expired} أسماء، {stats_expired} إحصائيات")
                
                # تنظيف المستخدمين غير النشطين (كل 6 ساعات)
‏                if now.hour % 6 == 0 and now.minute < 5:
‏                    if self.last_cleanup is None or (now - self.last_cleanup) > timedelta(hours=1):
‏                        UserManager.cleanup_inactive(config.inactive_days)
‏                        self.last_cleanup = now
            
‏            except Exception as e:
‏                logger.error(f"❌ خطأ في مهمة التنظيف: {e}")
    
‏    def start(self, active_games=None, games_lock=None):
        """بدء خيط التنظيف"""
‏        from config import config
        
‏        if active_games is None:
‏            active_games = {}
‏        if games_lock is None:
‏            import threading
‏            games_lock = threading.Lock()
        
‏        thread = threading.Thread(
‏            target=self.cleanup_task, 
‏            args=(active_games, games_lock, config),
‏            daemon=True
        )
‏        thread.start()
‏        logger.info("✅ بدء خيط التنظيف التلقائي")
‏        return thread
    
‏    def stop(self):
        """إيقاف التنظيف"""
‏        self.running = False
‏        logger.info("⏹️ تم إيقاف التنظيف التلقائي")

# إنشاء instance
‏cleanup_manager = CleanupManager()
