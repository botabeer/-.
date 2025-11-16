‏from linebot.models import TextSendMessage
‏import random
‏import logging

‏logger = logging.getLogger("whale-bot")

‏class CompatibilityGame:
‏    def __init__(self, line_bot_api):
‏        self.line_bot_api = line_bot_api
‏        self.waiting_for_names = True
    
‏    def start_game(self):
‏        return TextSendMessage(
‏            text="▪️ لعبة التوافق\n\n▫️ اكتب اسمين مفصولين بمسافة\n\n💡 مثال: اسم اسم"
        )
    
‏    def check_answer(self, answer, user_id, display_name):
‏        if not self.waiting_for_names:
‏            return None
        
‏        parts = answer.strip().split()
        
‏        if len(parts) < 2:
‏            return {
‏                'response': TextSendMessage(
‏                    text="⚠️ يجب كتابة اسمين مفصولين بمسافة\n\n💡 مثال: اسم اسم"
                ),
‏                'points': 0,
‏                'correct': False,
‏                'won': False,
‏                'game_over': False
            }
        
‏        name1 = parts[0]
‏        name2 = ' '.join(parts[1:])
        
        # حساب نسبة التوافق
‏        compatibility = random.randint(50, 100)
        
        # تحديد الرسالة
‏        if compatibility >= 90:
‏            message = " توافق مثالي"
‏            emoji = ""
‏        elif compatibility >= 75:
‏            message = " توافق ممتاز"
‏            emoji = ""
‏        elif compatibility >= 60:
‏            message = " توافق جيد"
‏            emoji = ""
‏        else:
‏            message = " توافق متوسط"
‏            emoji = ""
        
‏        self.waiting_for_names = False
        
‏        return {
‏            'response': TextSendMessage(
‏                text=f"▪️ نسبة التوافق\n\n{name1} 🖤 {name2}\n\n{emoji} {compatibility}%\n\n{message}"
            ),
‏            'points': 5,
‏            'correct': True,
‏            'won': True,
‏            'game_over': True
        }
