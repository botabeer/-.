from linebot.models import TextSendMessage
import random, re

class OppositeGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.all_words = [
            {"word": "كبير", "opposite": "صغير"},
            {"word": "طويل", "opposite": "قصير"},
            {"word": "سريع", "opposite": "بطيء"},
            {"word": "ساخن", "opposite": "بارد"},
            {"word": "نظيف", "opposite": "وسخ"},
            {"word": "قوي", "opposite": "ضعيف"},
            {"word": "سهل", "opposite": "صعب"},
            {"word": "جميل", "opposite": "قبيح"},
            {"word": "غني", "opposite": "فقير"},
            {"word": "فوق", "opposite": "تحت"}
        ]
        self.questions = []
        self.current_word = None
        self.hints_used = 0
        self.question_number = 0
        self.total_questions = 5
        self.player_scores = {}
    
    def normalize(self, text):
        if not text: return ""
        text = text.strip().lower()
        text = text.replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ؤ','و').replace('ئ','ي').replace('ء','').replace('ة','ه').replace('ى','ي')
        return re.sub(r'[\u064B-\u065F]', '', re.sub(r'\s+', '', text))
    
    def start_game(self):
        self.questions = random.sample(self.all_words, self.total_questions)
        self.question_number = 0
        self.player_scores = {}
        return self._next_question()
    
    def _next_question(self):
        self.question_number += 1
        self.current_word = self.questions[self.question_number - 1]
        self.hints_used = 0
        return TextSendMessage(text=f"▪️ لعبة الأضداد\n\n▫️ سؤال {self.question_number} من {self.total_questions}\n\n▫️ ما عكس: {self.current_word['word']}\n\n▪️ مثال: كبير → صغير\n▪️ لمح - تلميح\n▪️ جاوب - الحل")
    
    def next_question(self):
        return self._next_question() if self.question_number < self.total_questions else None
    
    def check_answer(self, answer, user_id, name):
        if not self.current_word:
            return None
        
        answer_lower = answer.strip().lower()
        
        if answer_lower in ['لمح', 'تلميح']:
            if self.hints_used == 0:
                opposite = self.current_word['opposite']
                self.hints_used += 1
                return {'response': TextSendMessage(text=f"▫️ يبدأ بحرف: {opposite[0]}\n▫️ عدد الحروف: {len(opposite)}"), 'points': 0, 'correct': False}
            return {'response': TextSendMessage(text="▫️ استخدمت التلميح"), 'points': 0, 'correct': False}
        
        if answer_lower in ['جاوب', 'الجواب', 'الحل']:
            return {'response': TextSendMessage(text=f"▪️ الإجابة: {self.current_word['opposite']}"), 'points': 0, 'correct': False, 'next_question': True}
        
        if self.normalize(answer) == self.normalize(self.current_word['opposite']):
            points = 15 - (self.hints_used * 3)
            
            if user_id not in self.player_scores:
                self.player_scores[user_id] = {'name': name, 'score': 0}
            self.player_scores[user_id]['score'] += points
            
            if self.question_number < self.total_questions:
                return {'response': TextSendMessage(text=f"▪️ صحيح {name}\n\n▫️ {self.current_word['word']} ↔️ {self.current_word['opposite']}\n▫️ +{points} نقطة"), 'points': points, 'correct': True, 'won': True, 'next_question': True}
            
            return self._end_game()
        
        return None
    
    def _end_game(self):
        if self.player_scores:
            sorted_players = sorted(self.player_scores.items(), key=lambda x: x[1]['score'], reverse=True)
            winner = sorted_players[0][1]
            return {'response': TextSendMessage(text=f"▪️ انتهت اللعبة\n\n▫️ الفائز: {winner['name']}\n▫️ النقاط: {winner['score']}"), 'points': 0, 'game_over': True}
        return {'response': TextSendMessage(text="▪️ انتهت اللعبة"), 'points': 0, 'game_over': True}
