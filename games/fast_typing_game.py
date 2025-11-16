from linebot.models import TextSendMessage
import random
import re
from datetime import datetime, timedelta

class FastTypingGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.current_word = None
        self.first_correct = None
        self.start_time = None
        self.time_limit = 30
        self.scores = {}
        
        self.words = [
            "سرعة", "كتابة", "برمجة", "حاسوب", "إنترنت", "تطبيق", "موقع", "شبكة",
            "تقنية", "ذكاء", "نجم", "تطوير", "مبرمج", "لغة", "كود", "برنامج",
            "نظام", "بيانات", "معلومات", "أمان", "حماية", "تشفير", "خوارزمية", "كواكب"
        ]
    
    def normalize_text(self, text):
        if not text:
            return ""
        text = text.strip().lower()
        text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
        text = text.replace('ؤ', 'و').replace('ئ', 'ي').replace('ء', '')
        text = text.replace('ة', 'ه').replace('ى', 'ي')
        text = re.sub(r'[\u064B-\u065F]', '', text)
        text = re.sub(r'\s+', '', text)
        return text
    
    def start_game(self):
        self.current_word = random.choice(self.words)
        self.first_correct = None
        self.start_time = datetime.now()
        self.scores = {}
        
        return TextSendMessage(text=f"▪️ لعبة الكتابة السريعة\n\nاكتب هذه الكلمة بأسرع وقت:\n\n{self.current_word}\n\n⏱️ لديك {self.time_limit} ثانية")
    
    def check_answer(self, text, user_id, display_name):
        if self.start_time and (datetime.now() - self.start_time).seconds > self.time_limit:
            if not self.first_correct:
                return {
                    'correct': False,
                    'game_over': True,
                    'response': TextSendMessage(text=f"▫️ انتهى الوقت\n\nلم يجب أحد بشكل صحيح\n\nالكلمة: {self.current_word}")
                }
            return None
        
        if self.first_correct:
            return None
        
        text_normalized = self.normalize_text(text)
        word_normalized = self.normalize_text(self.current_word)
        
        if text_normalized == word_normalized:
            elapsed_time = (datetime.now() - self.start_time).total_seconds()
            points = max(2, int(10 - elapsed_time / 3))
            
            self.first_correct = user_id
            if user_id not in self.scores:
                self.scores[user_id] = {'name': display_name, 'score': 0}
            self.scores[user_id]['score'] += points
            
            return {
                'correct': True,
                'points': points,
                'won': True,
                'game_over': True,
                'response': TextSendMessage(text=f"🏆 {display_name} فاز\n\nالوقت: {elapsed_time:.2f} ثانية\n+{points} نقطة")
            }
        
        return None
