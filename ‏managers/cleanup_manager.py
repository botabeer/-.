from database import db_manager
from datetime import datetime, timedelta
import logging

logger = logging.getLogger("whale-bot")

class CleanupManager:
    """تنظيف البيانات القديمة وغير النشطة"""

    def __init__(self, inactive_days: int = 45):
        self.db = db_manager
        self.inactive_days = inactive_days

    def cleanup_inactive_users(self):
        cutoff = datetime.now() - timedelta(days=self.inactive_days)
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "DELETE FROM players WHERE last_active < ?", (cutoff,)
        )
        conn.commit()
        logger.info("✅ تم تنظيف المستخدمين غير النشطين")

# إنشاء instance جاهز للاستخدام
cleanup_manager = CleanupManager()
