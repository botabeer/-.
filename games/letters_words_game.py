from linebot.models import TextSendMessage
import random
import re

class LettersWordsGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.current_letter = None
        self.used_words = set()
    
    def start_game(self):
        self.current_letter = random.choice(list("أبتثجحخدذرزسشصضطظعغفقكلمنهوي"))
        self.used_words = set()
        return TextSendMessage(text=f"▪️ اكتب كلمة تبدأ بحرف:\n{self.current_letter}")
    
    def check_answer(self, text, user_id, display_name):
        word = text.strip()
        
        if not word.startswith(self.current_letter):
            return {"response": TextSendMessage(text="▫️ يجب أن تبدأ الكلمة بالحرف المطلوب")}
        
        if word in self.used_words:
            return {"response": TextSendMessage(text="▫️ الكلمة مستخدمة مسبقًا")}
        
        self.used_words.add(word)
        
        return {
            "correct": True,
            "response": TextSendMessage(text=f"▪️ ممتاز {display_name}! +1 نقطة")
        }
