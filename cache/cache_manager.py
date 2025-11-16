from threading import Lock
from datetime import datetime, timedelta

class CacheManager:
    def __init__(self, max_size=1000, ttl=3600):
        self.cache = {}
        self.max_size = max_size
        self.ttl = ttl  # بالثواني
        self.lock = Lock()

    def set(self, key, value):
        with self.lock:
            if len(self.cache) >= self.max_size:
                # إزالة العنصر الأقدم
                oldest_key = min(self.cache, key=lambda k: self.cache[k]['time'])
                del self.cache[oldest_key]
            self.cache[key] = {'value': value, 'time': datetime.now()}

    def get(self, key):
        with self.lock:
            item = self.cache.get(key)
            if not item:
                return None
            if (datetime.now() - item['time']).total_seconds() > self.ttl:
                del self.cache[key]
                return None
            return item['value']

    def clear(self):
        with self.lock:
            self.cache.clear()
