from linebot.models import TextSendMessage
import random
import re

def normalize_text(text):
    if not text:
        return ""
    text = text.strip().lower()
    text = text.replace('أ', 'ا').replace('إ', 'ا').replace('آ', 'ا')
    text = text.replace('ؤ', 'و').replace('ئ', 'ي').replace('ء', '')
    text = text.replace('ة', 'ه').replace('ى', 'ي')
    text = re.sub(r'[\u064B-\u065F]', '', text)
    text = re.sub(r'\s+', '', text)
    return text

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
            {"word": "فوق", "opposite": "تحت"},
            {"word": "يمين", "opposite": "يسار"},
            {"word": "أمام", "opposite": "خلف"},
            {"word": "داخل", "opposite": "خارج"},
            {"word": "قريب", "opposite": "بعيد"},
            {"word": "جديد", "opposite": "قديم"}
        ]
        
        self.questions = []
        self.current_word = None
        self.hints_used = 0
        self.question_number = 0
        self.total_questions = 5
        self.player_scores = {}
    
    def start_game(self):
        self.questions = random.sample(self.all_words, self.total_questions)
        self.question_number = 0
        self.player_scores = {}
        return self._next_question()
    
    def _next_question(self):
        self.question_number += 1
        self.current_word = self.questions[self.question_number - 1]
        self.hints_used = 0
        return TextSendMessage(text=f"▪️ لعبة الأضداد\n\nسؤال {self.question_number} من {self.total_questions}\n\nما هو عكس كلمة: {self.current_word['word']}\n\n▫️ لمح - للحصول على تلميح\n▫️ جاوب - لعرض الإجابة")
    
    def next_question(self):
        if self.question_number < self.total_questions:
            return self._next_question()
        return None
    
    def check_answer(self, answer, user_id, display_name):
        if not self.current_word:
            return None
        
        answer_lower = answer.strip().lower()
        
        if answer_lower in ['لمح', 'تلميح', 'hint']:
            if self.hints_used == 0:
                opposite = self.current_word['opposite']
                first_letter = opposite[0]
                word_length = len(opposite)
                hint = f"▫️ يبدأ بحرف: {first_letter}\n▫️ عدد الحروف: {word_length}"
                self.hints_used += 1
                return {
                    'response': TextSendMessage(text=hint),
                    'points': -1,
                    'correct': False,
                    'won': False,
                    'game_over': False
                }
            else:
                return {
                    'response': TextSendMessage(text="▫️ استخدمت التلميح"),
                    'points': 0,
                    'correct': False,
                    'won': False,
                    'game_over': False
                }
        
        if answer_lower in ['جاوب', 'الجواب', 'answer']:
            response_text = f"▪️ الإجابة: {self.current_word['opposite']}"
            if self.question_number < self.total_questions:
                return {
                    'response': TextSendMessage(text=response_text),
                    'points': 0,
                    'correct': False,
                    'won': False,
                    'game_over': False,
                    'next_question': True
                }
            else:
                return self._end_game()
        
        if normalize_text(answer) == normalize_text(self.current_word['opposite']):
            points = 2 - self.hints_used
            if user_id not in self.player_scores:
                self.player_scores[user_id] = {'name': display_name, 'score': 0}
            self.player_scores[user_id]['score'] += points
            
            if self.question_number < self.total_questions:
                response_text = f"▪️ صحيح {display_name}\n\n{self.current_word['word']} ↔️ {self.current_word['opposite']}\n\n+{points} نقطة"
                return {
                    'response': TextSendMessage(text=response_text),
                    'points': points,
                    'correct': True,
                    'won': True,
                    'game_over': False,
                    'next_question': True
                }
            else:
                return self._end_game()
        
        return None
    
    def _end_game(self):
        if self.player_scores:
            sorted_players = sorted(self.player_scores.items(), key=lambda x: x[1]['score'], reverse=True)
            winner = sorted_players[0][1]
            all_scores = [(data['name'], data['score']) for uid, data in sorted_players]
            
            from app import get_winner_card
            winner_card = get_winner_card(winner['name'], winner['score'], all_scores)
            
            return {
                'points': 0,
                'correct': False,
                'won': True,
                'game_over': True,
                'winner_card': winner_card
            }
        else:
            return {
                'response': TextSendMessage(text="▫️ انتهت اللعبة"),
                'points': 0,
                'correct': False,
                'won': False,
                'game_over': True
            }
