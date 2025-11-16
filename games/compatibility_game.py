‏# ═══════════════════════════════════════════════════════════════
# games/compatibility_game.py - لعبة التوافق الذكية
# ═══════════════════════════════════════════════════════════════
from linebot.models import TextSendMessage
import hashlib
import logging

logger = logging.getLogger("whale-bot")

class CompatibilityGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.waiting_for_names = True
    
    def normalize_name(self, name):
        """تطبيع الاسم للمقارنة"""
        if not name:
            return ""
        name = name.strip().lower()
        name = name.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
        name = name.replace('ة', 'ه').replace('ى', 'ي')
        import re
        name = re.sub(r'[\u064B-\u065F]', '', name)
        return name
    
    def calculate_compatibility(self, name1, name2):
        """حساب نسبة التوافق (ثابتة دائماً لنفس الأسماء)"""
        normalized1 = self.normalize_name(name1)
        normalized2 = self.normalize_name(name2)
        
        if normalized1 > normalized2:
            normalized1, normalized2 = normalized2, normalized1
        
        combined = normalized1 + normalized2
        hash_value = int(hashlib.md5(combined.encode('utf-8')).hexdigest(), 16)
        compatibility = 50 + (hash_value % 51)
        return compatibility
    
    def get_compatibility_message(self, compatibility):
        if compatibility >= 90:
            return " توافق مثالي", ""
        elif compatibility >= 75:
            return " توافق ممتاز", ""
        elif compatibility >= 60:
            return " توافق جيد", ""
        else:
            return " توافق متوسط", ""
    
    def start_game(self):
        return TextSendMessage(
            text="▪️ لعبة التوافق 🖤\n\n▫️ اكتب اسمين مفصولين بمسافة\n\n💡 مثال: اسم اسم"
        )
    
    def check_answer(self, answer, user_id, display_name):
        if not self.waiting_for_names:
            return None
        
        parts = answer.strip().split()
        
        if len(parts) < 2:
            return {
                'response': TextSendMessage(
                    text="⚠️ يجب كتابة اسمين مفصولين بمسافة\n\n💡 مثال: اسم اسم"
                ),
                'points': 0,
                'correct': False,
                'won': False,
                'game_over': False
            }
        
        name1 = parts[0]
        name2 = ' '.join(parts[1:])
        
        compatibility = self.calculate_compatibility(name1, name2)
        message, emoji = self.get_compatibility_message(compatibility)

        self.waiting_for_names = False
        
        result_text = (
            f"▪️ نسبة التوافق\n\n"
            f"{name1} 🖤 {name2}\n\n"
            f"{emoji} {compatibility}%\n\n"
            f"{message}"
        )
        
        logger.info(f"توافق: {name1} + {name2} = {compatibility}%")
        
        return {
            'response': TextSendMessage(text=result_text),
            'points': 5,
            'correct': True,
            'won': True,
            'game_over': True
        }
