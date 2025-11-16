from .cache_manager import CacheManager

# إنشاء الـ singleton objects للاستخدام في المشروع
names_cache = CacheManager()
stats_cache = CacheManager()
leaderboard_cache = CacheManager()

__all__ = ['names_cache', 'stats_cache', 'leaderboard_cache', 'CacheManager']
