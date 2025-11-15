from linebot.models import TextSendMessage
import random

class CompatibilityGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.waiting_for_names = True
    
    def start_game(self):
        return TextSendMessage(
            text="▪️ لعبة التوافق\n\naكتب اسمين مفصولين بمسافة\nمثال: أحمد فاطمة"
        )
    
    def check_answer(self, answer, user_id, display_name):
        if not self.waiting_for_names:
            return None
        
        parts = answer.strip().split()
        
        if len(parts) < 2:
            return {
                'response': TextSendMessage(
                    text="يجب كتابة اسمين مفصولين بمسافة"
                ),
                'points': 0,
                'correct': False,
                'won': False,
                'game_over': False
            }
        
        name1 = parts[0]
        name2 = ' '.join(parts[1:])
        
        compatibility = random.randint(50, 100)
        
        if compatibility >= 90:
            message = "توافق مثالي"
        elif compatibility >= 75:
            message = "توافق ممتاز"
        elif compatibility >= 60:
            message = "توافق جيد"
        else:
            message = "توافق متوسط"
        
        self.waiting_for_names = False
        
        return {
            'response': TextSendMessage(
                text=f"▪️ نسبة التوافق\n\n{name1} ▪️ {name2}\n\n▫️ {compatibility}%\n\n{message}"
            ),
            'points': 5,
            'correct': True,
            'won': True,
            'game_over': True
        }
