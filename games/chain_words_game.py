# ============================================
# chain_words_game.py - لعبة سلسلة الكلمات
# ============================================

from linebot.models import TextSendMessage
import random
import re

class ChainWordsGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.start_words = ["قلم", "كتاب", "مدرسة", "باب", "نافذة", "طاولة"]
        self.current_word = None
        self.used_words = set()
        self.round_count = 0
        self.max_rounds = 5
        self.player_scores = {}
    
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
        self.current_word = random.choice(self.start_words)
        self.used_words = {self.normalize_text(self.current_word)}
        self.round_count = 0
        self.player_scores = {}
        return TextSendMessage(
            text=f"▪️ لعبة سلسلة الكلمات\n\n▫️ الكلمة: {self.current_word}\n▫️ اكتب كلمة تبدأ بحرف: {self.current_word[-1]}\n\n▪️ مثال: قلم → ملك → كتاب\n▪️ الجولات: {self.max_rounds}"
        )
    
    def next_question(self):
        if self.round_count < self.max_rounds:
            last_letter = self.current_word[-1]
            return TextSendMessage(
                text=f"▪️ جولة {self.round_count + 1} من {self.max_rounds}\n\n▫️ الكلمة السابقة: {self.current_word}\n▫️ اكتب كلمة تبدأ بـ: {last_letter}"
            )
        return None
    
    def check_answer(self, answer, user_id, display_name):
        if not self.current_word:
            return None
        
        answer = answer.strip()
        last_letter = self.current_word[-1]
        normalized_last = 'ه' if last_letter in ['ة', 'ه'] else last_letter
        normalized_answer = self.normalize_text(answer)
        
        if normalized_answer in self.used_words:
            return {'response': TextSendMessage(text="▫️ هذه الكلمة استخدمت"), 'points': 0, 'correct': False, 'won': False, 'game_over': False}
        
        first_letter = 'ه' if answer[0].lower() in ['ة', 'ه'] else answer[0].lower()
        
        if first_letter == normalized_last:
            self.used_words.add(normalized_answer)
            old_word = self.current_word
            self.current_word = answer
            self.round_count += 1
            
            points = 10
            if user_id not in self.player_scores:
                self.player_scores[user_id] = {'name': display_name, 'score': 0}
            self.player_scores[user_id]['score'] += points
            
            if self.round_count < self.max_rounds:
                return {
                    'response': TextSendMessage(text=f"▪️ صحيح {display_name}\n\n▫️ {old_word} ← {answer}\n▫️ +{points} نقطة"),
                    'points': points, 'correct': True, 'won': True, 'game_over': False, 'next_question': True
                }
            else:
                return self._end_game()
        else:
            return {'response': TextSendMessage(text=f"▫️ يجب أن تبدأ بحرف: {last_letter}"), 'points': 0, 'correct': False, 'won': False, 'game_over': False}
    
    def _end_game(self):
        if self.player_scores:
            sorted_players = sorted(self.player_scores.items(), key=lambda x: x[1]['score'], reverse=True)
            winner = sorted_players[0][1]
            all_scores = [(data['name'], data['score']) for uid, data in sorted_players]
            message = f"▪️ انتهت اللعبة\n\n▫️ الفائز: {winner['name']}\n▫️ النقاط: {winner['score']}"
            return {'response': TextSendMessage(text=message), 'points': 0, 'correct': False, 'won': False, 'game_over': True}
        else:
            return {'response': TextSendMessage(text="▪️ انتهت اللعبة"), 'points': 0, 'correct': False, 'won': False, 'game_over': True}
