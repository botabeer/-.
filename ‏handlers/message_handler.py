from linebot.models import TextSendMessage
from managers.user_manager import UserManager
from managers.game_manager import GameManager
from managers.cleanup_manager import cleanup_manager
from utils import safe_text, check_rate
import logging

logger = logging.getLogger("whale-bot")

user_manager = UserManager()
game_manager = GameManager()

# لتتبع عدد الرسائل لكل مستخدم في الوقت الحالي
user_message_count = {}

def handle_message(user_id: str, message_text: str, line_bot_api):
    """
    معالجة الرسائل الواردة من المستخدم
    """
    message_text = safe_text(message_text)

    # تحقق معدل الرسائل
    if user_id not in user_message_count:
        user_message_count[user_id] = {'count': 0, 'reset_time': None}
    
    if not check_rate(user_id, user_message_count):
        return TextSendMessage(text="⚠️ لقد وصلت الحد الأقصى للرسائل، حاول لاحقاً.")

    # تنظيف الرسالة
    message_text = message_text.strip()

    # مثال على التحقق من أوامر الألعاب
    if message_text.startswith("لعبة:"):
        game_name = message_text.split(":", 1)[1].strip()
        logger.info(f"تشغيل اللعبة: {game_name} للمستخدم {user_id}")
        return TextSendMessage(text=f"جارٍ تشغيل اللعبة {game_name}...")

    # مثال على رسائل عامة
    return TextSendMessage(text=f"مرحباً {user_manager.get_display_name(user_id)}! لم يتم التعرف على الأمر.")
