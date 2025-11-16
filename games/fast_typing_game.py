from linebot.models import TextSendMessage
import random
import time

class FastTypingGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.current_text = None
        self.start_time = None
        self.winner = None
        
        self.words = [
            "قلب", "أمل", "سرعة", "سيارة", "برمجة", "كمبيوتر", 
            "تفاحة", "مستقبل", "ذكاء", "حديقة", "مدينة", "نجم"
        ]
    
    def start_game(self):
        self.current_text = random.choice(self.words)
        self.start_time = time.time()
        self.winner = None
        return TextSendMessage(text=f"▪️ اكتب الجملة التالية بسرعة:\n\n{self.current_text}")
    
    def check_answer(self, text, user_id, display_name):
        if self.winner:
            return None
        
        if text.strip() == self.current_text:
            self.winner = user_id
            time_taken = round(time.time() - self.start_time, 2)
            return {
                "correct": True,
                "response": TextSendMessage(
                    text=f"▪️ مبروك {display_name}!\nكتبتها في {time_taken} ثانية"
                )
            }
        
        return None
