from linebot.models import TextSendMessage
import random
import re

def normalize_text(text):
    if not text:
        return ""
    text = text.strip().lower()
    text = text.replace('أ','ا').replace('إ','ا').replace('آ','ا')
    text = text.replace('ؤ','و').replace('ئ','ي').replace('ء','')
    text = text.replace('ة','ه').replace('ى','ي')
    text = re.sub(r'[\u064B-\u065F]','', text)
    text = re.sub(r'\s+','', text)
    return text

class ChainWordsGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.start_words = ["قلم","كتاب","مدرسة","باب","نافذة","طاولة","كرسي","حديقة","شجرة","زهرة"]
        self.current_word = None
        self.used_words = set()
        self.round_count = 0
        self.max_rounds = 5
        self.player_scores = {}
    
    def start_game(self):
        self.current_word = random.choice(self.start_words)
        self.used_words = {normalize_text(self.current_word)}
        self.round_count = 0
        self.player_scores = {}
        return TextSendMessage(text=f"▪️ لعبة سلسلة الكلمات\nالكلمة: {self.current_word}")
    
    def check_answer(self, answer, user_id, display_name):
        if not self.current_word:
            return None
        
        answer = answer.strip()
        last_letter = self.current_word[-1]
        normalized_answer = normalize_text(answer)
        
        if normalized_answer in self.used_words:
            return {"response": TextSendMessage(text="▫️ الكلمة مستخدمة مسبقًا")}
        
        if answer[0] != last_letter:
            return {"response": TextSendMessage(text=f"▫️ يجب أن تبدأ الكلمة بحرف: {last_letter}")}
        
        self.used_words.add(normalized_answer)
        self.current_word = answer
        self.round_count += 1
        
        points = 2
        if user_id not in self.player_scores:
            self.player_scores[user_id] = {'name': display_name, 'score': 0}
        self.player_scores[user_id]['score'] += points
        
        if self.round_count >= self.max_rounds:
            return {"response": TextSendMessage(text="▫️ انتهت اللعبة")}
        
        return {
            "response": TextSendMessage(text=f"▪️ ممتاز {display_name}\n+{points} نقطة"),
            "next_question": True
        }
