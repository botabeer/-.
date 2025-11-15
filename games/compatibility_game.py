from linebot.models import TextSendMessage
import random

class CompatibilityGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.waiting_for_names = True
    
    def start_game(self):
        return TextSendMessage(text="▪️ لعبة التوافق\n\nاكتب اسمين مفصولين بمسافة\nنص فقط بدون رموز\n\nمثال: محمد فاطمة")
    
    def check_answer(self, answer, user_id, display_name):
        if not self.waiting_for_names:
            return None
        
        parts = answer.strip().split()
        
        if len(parts) < 2:
            return {
                'response': TextSendMessage(text="▫️ يجب كتابة اسمين مفصولين بمسافة\n\nمثال: محمد فاطمة"),
                'points': 0,
                'correct': False,
                'won': False,
                'game_over': False
            }
        
        name1 = parts[0]
        name2 = ' '.join(parts[1:])
        
        # حساب نسبة التوافق
        compatibility = random.randint(60, 100)
        
        if compatibility >= 90:
            status = "توافق مثالي "
        elif compatibility >= 80:
            status = "توافق ممتاز "
        elif compatibility >= 70:
            status = "توافق جيد "
        else:
            status = "توافق متوسط "
        
        self.waiting_for_names = False
        
        return {
            'response': TextSendMessage(
                text=f"▪️ نسبة التوافق\n\n{name1} 🖤 {name2}\n\n▫️ {compatibility}%\n\n{status}\n\nملاحظة: هذه اللعبة للتسلية فقط"
            ),
            'points': 0,  # لا نقاط لهذه اللعبة
            'correct': True,
            'won': True,
            'game_over': True
        }
