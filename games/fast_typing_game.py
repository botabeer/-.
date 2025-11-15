from linebot.models import TextSendMessage
from datetime import datetime
import random, re

class FastTypingGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.current_word = None
        self.first_correct = None
        self.start_time = None
        self.time_limit = 30
        self.scores = {}
        self.words = ["سرعة","كتابة","برمجة","حاسوب","إنترنت","تطبيق","موقع","شبكة","تقنية","ذكاء","تطوير","مبرمج"]
    
    def normalize(self, text):
        if not text: return ""
        text = text.strip().lower()
        text = text.replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ؤ','و').replace('ئ','ي').replace('ء','').replace('ة','ه').replace('ى','ي')
        return re.sub(r'[\u064B-\u065F]', '', re.sub(r'\s+', '', text))
    
    def start_game(self):
        self.current_word = random.choice(self.words)
        self.first_correct = None
        self.start_time = datetime.now()
        self.scores = {}
        return TextSendMessage(text=f"▪️ لعبة الكتابة السريعة\n\n▫️ اكتب هذه الكلمة:\n\n{self.current_word}\n\n▫️ الوقت: {self.time_limit} ثانية\n▫️ أول إجابة صحيحة تفوز")
    
    def check_answer(self, text, user_id, name):
        if self.start_time:
            elapsed = (datetime.now() - self.start_time).seconds
            if elapsed > self.time_limit:
                if not self.first_correct:
                    return {'correct': False, 'game_over': True, 'response': TextSendMessage(text=f"▪️ انتهى الوقت\n\n▫️ لم يجب أحد\n▫️ الكلمة: {self.current_word}")}
                return None
        
        if self.first_correct:
            return None
        
        if self.normalize(text) == self.normalize(self.current_word):
            elapsed_time = (datetime.now() - self.start_time).total_seconds()
            points = 20 if elapsed_time <= 5 else 15 if elapsed_time <= 10 else 10 if elapsed_time <= 20 else 5
            
            self.first_correct = user_id
            if user_id not in self.scores:
                self.scores[user_id] = {'name': name, 'score': 0}
            self.scores[user_id]['score'] += points
            
            return {'correct': True, 'points': points, 'won': True, 'game_over': True, 'response': TextSendMessage(text=f"▪️ {name} فاز\n\n⏱️ الوقت: {elapsed_time:.2f} ثانية\n▫️ النقاط: +{points}")}
        
        return None
