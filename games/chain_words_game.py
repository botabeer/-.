from linebot.models import TextSendMessage
import random, re

class ChainWordsGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.start_words = ["قلم","كتاب","مدرسة","باب","نافذة","طاولة","جبل","بحر","شمس","قمر"]
        self.current_word = None
        self.used_words = set()
        self.round_count = 0
        self.max_rounds = 5
        self.player_scores = {}
    
    def normalize(self, text):
        if not text: return ""
        text = text.strip().lower()
        text = text.replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ؤ','و').replace('ئ','ي').replace('ء','').replace('ة','ه').replace('ى','ي')
        return re.sub(r'[\u064B-\u065F]', '', re.sub(r'\s+', '', text))
    
    def start_game(self):
        self.current_word = random.choice(self.start_words)
        self.used_words = {self.normalize(self.current_word)}
        self.round_count = 0
        self.player_scores = {}
        return TextSendMessage(text=f"▪️ لعبة سلسلة الكلمات\n\n▫️ الكلمة: {self.current_word}\n▫️ اكتب كلمة تبدأ بحرف: {self.current_word[-1]}\n\n▪️ مثال: قلم → ملك → كتاب\n▪️ الجولات: {self.max_rounds}")
    
    def next_question(self):
        return TextSendMessage(text=f"▪️ جولة {self.round_count + 1} من {self.max_rounds}\n\n▫️ الكلمة السابقة: {self.current_word}\n▫️ اكتب كلمة تبدأ بـ: {self.current_word[-1]}") if self.round_count < self.max_rounds else None
    
    def check_answer(self, answer, user_id, name):
        if not self.current_word:
            return None
        
        last_letter = self.current_word[-1]
        norm_last = 'ه' if last_letter in ['ة','ه'] else last_letter
        norm_answer = self.normalize(answer)
        
        if norm_answer in self.used_words:
            return {'response': TextSendMessage(text="▫️ هذه الكلمة استخدمت"), 'points': 0, 'correct': False}
        
        first = 'ه' if answer[0].lower() in ['ة','ه'] else answer[0].lower()
        
        if first == norm_last:
            self.used_words.add(norm_answer)
            old = self.current_word
            self.current_word = answer
            self.round_count += 1
            
            points = 10
            if user_id not in self.player_scores:
                self.player_scores[user_id] = {'name': name, 'score': 0}
            self.player_scores[user_id]['score'] += points
            
            if self.round_count < self.max_rounds:
                return {'response': TextSendMessage(text=f"▪️ صحيح {name}\n\n▫️ {old} ← {answer}\n▫️ +{points} نقطة"), 'points': points, 'correct': True, 'won': True, 'next_question': True}
            
            return self._end_game()
        
        return {'response': TextSendMessage(text=f"▫️ يجب أن تبدأ بحرف: {last_letter}"), 'points': 0, 'correct': False}
    
    def _end_game(self):
        if self.player_scores:
            sorted_players = sorted(self.player_scores.items(), key=lambda x: x[1]['score'], reverse=True)
            winner = sorted_players[0][1]
            return {'response': TextSendMessage(text=f"▪️ انتهت اللعبة\n\n▫️ الفائز: {winner['name']}\n▫️ النقاط: {winner['score']}"), 'points': 0, 'game_over': True}
        return {'response': TextSendMessage(text="▪️ انتهت اللعبة"), 'points': 0, 'game_over': True}
