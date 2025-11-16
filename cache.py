‏import threading
‏from datetime import datetime
‏from typing import Dict, Tuple, Optional

‏class CacheManager:
    """مدير الذاكرة المؤقتة"""
    
‏    def __init__(self, max_size: int = 1000, ttl: int = 3600):
‏        self.max_size = max_size
‏        self.ttl = ttl
‏        self.cache: Dict[str, Tuple[any, datetime]] = {}
‏        self.lock = threading.Lock()
    
‏    def get(self, key: str) -> Optional[any]:
        """الحصول على قيمة من الذاكرة"""
‏        with self.lock:
‏            if key in self.cache:
‏                value, timestamp = self.cache[key]
‏                if (datetime.now() - timestamp).seconds < self.ttl:
‏                    return value
‏                else:
‏                    del self.cache[key]
‏        return None
    
‏    def set(self, key: str, value: any) -> None:
        """حفظ قيمة في الذاكرة"""
‏        with self.lock:
‏            if len(self.cache) >= self.max_size:
‏                oldest_key = min(self.cache.items(), key=lambda x: x[1][1])[0]
‏                del self.cache[oldest_key]
‏            self.cache[key] = (value, datetime.now())
    
‏    def delete(self, key: str) -> None:
        """حذف قيمة من الذاكرة"""
‏        with self.lock:
‏            self.cache.pop(key, None)
    
‏    def clear(self) -> None:
        """مسح الذاكرة"""
‏        with self.lock:
‏            self.cache.clear()
    
‏    def cleanup(self) -> int:
        """حذف القيم منتهية الصلاحية"""
‏        with self.lock:
‏            now = datetime.now()
‏            expired_keys = [
‏                k for k, (_, ts) in self.cache.items()
‏                if (now - ts).seconds >= self.ttl
            ]
‏            for key in expired_keys:
‏                del self.cache[key]
‏            return len(expired_keys)

‏from config import config
‏names_cache = CacheManager(max_size=config.names_cache_max, ttl=3600)
‏stats_cache = CacheManager(max_size=500, ttl=60)
‏leaderboard_cache = CacheManager(max_size=1, ttl=60)
