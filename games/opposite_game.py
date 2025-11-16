from linebot.models import TextSendMessage
import random

class OppositeGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.current_word = None
        self.answered = False
        
        self.words = {
            "سريع": "بطيء",
            "ليل": "نهار",
            "كبير": "صغير",
            "قوي": "ضعيف",
            "قديم": "جديد",
            "سهل": "صعب",
            "سعيد": "حزين",
            "فاخر": "رخيص",
        }
    
    def start_game(self):
        self.current_word = random.choice(list(self.words))
        self.answered = False
        return TextSendMessage(text=f"▪️ ما هو ضد كلمة:\n{self.current_word}")
    
    def check_answer(self, text, user_id, display_name):
        if self.answered:
            return None
        
        if text.strip() == self.words[self.current_word]:
            self.answered = True
            return {
                "correct": True,
                "response": TextSendMessage(text=f"▪️ صحيح {display_name}! +2 نقطة")
            }
        
        return None
