import threading
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional

class CacheManager:
    """
    مدير الذاكرة المؤقتة
    يخزن:
        - قيمة
        - وقت الانتهاء TTL
    """

    def __init__(self, max_size: int = 1000, ttl: int = 3600):
        self.max_size = max_size
        self.ttl = ttl
        self._cache: Dict[str, Tuple[any, datetime]] = {}
        self._lock = threading.Lock()

    def set(self, key: str, value: any, ttl: Optional[int] = None):
        """تخزين قيمة مع مدة صلاحية"""
        with self._lock:
            if len(self._cache) >= self.max_size:
                self._cleanup()

            lifetime = ttl if ttl is not None else self.ttl
            expire_time = datetime.now() + timedelta(seconds=lifetime)
            self._cache[key] = (value, expire_time)

    def get(self, key: str):
        """استرجاع قيمة إذا لم تنتهي صلاحيتها"""
        with self._lock:
            if key not in self._cache:
                return None

            value, expire_time = self._cache[key]

            if datetime.now() > expire_time:
                del self._cache[key]
                return None

            return value

    def delete(self, key: str):
        """حذف قيمة"""
        with self._lock:
            if key in self._cache:
                del self._cache[key]

    def clear(self):
        """مسح جميع القيم"""
        with self._lock:
            self._cache.clear()

    def _cleanup(self):
        """تنظيف العناصر المنتهية لتوفير مساحة"""
        now = datetime.now()
        expired_keys = [key for key, (_, t) in self._cache.items() if t < now]

        for key in expired_keys:
            del self._cache[key]
