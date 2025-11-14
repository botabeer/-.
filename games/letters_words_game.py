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

class LettersWordsGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.all_challenges = [
            {"letters": "م ح م د", "words": ["محمد", "مد", "حمد"], "min_length": 3},
            {"letters": "ك ت ا ب", "words": ["كتاب", "كاتب", "تكب"], "min_length": 3},
            {"letters": "م د ر س ة", "words": ["مدرسة", "درس", "مدر", "سرد"], "min_length": 3},
            {"letters": "ق ل م", "words": ["قلم", "لقم"], "min_length": 3},
            {"letters": "ب ي ت", "words": ["بيت", "تبي"], "min_length": 3},
            {"letters": "ش ج ر ة", "words": ["شجرة", "جرش", "شجر"], "min_length": 3},
            {"letters": "ح د ي ق ة", "words": ["حديقة", "حديق", "قديح"], "min_length": 3}
        ]
        self.questions = []
        self.current_challenge = None
        self.found_words = set()
        self.hints_used = 0
        self.question_number = 0
        self.total_questions = 5
        self.player_scores = {}
    
    def start_game(self):
        self.questions = random.sample(self.all_challenges, self.total_questions)
        self.question_number = 0
        self.player_scores = {}
        return self._next_question()
    
    def _next_question(self):
        self.question_number += 1
        self.current_challenge = self.questions[self.question_number - 1]
        self.found_words = set()
        self.hints_used = 0
        return TextSendMessage(
            text=f"▪️ لعبة تكوين الكلمات\n\nسؤال {self.question_number} من {self.total_questions}\n\nالحروف: {self.current_challenge['letters']}\n\nكون كلمة من هذه الحروف\n(على الأقل {self.current_challenge['min_length']} حروف)\n\n▫️ لمح - للحصول على تلميح\n▫️ جاوب - لعرض الإجابات"
        )
    
    def next_question(self):
        if self.question_number < self.total_questions:
            return self._next_question()
        return None
    
    def check_answer(self, answer, user_id, display_name):
        if not self.current_challenge:
            return None
        
        answer_lower = answer.strip().lower()
        
        if answer_lower in ['لمح', 'تلميح', 'hint']:
            if self.hints_used == 0:
                hint = f"▫️ مثال: {self.current_challenge['words'][0]}"
                self.hints_used += 1
                return {
                    'response': TextSendMessage(text=hint),
                    'points': 0,
                    'correct': False,
                    'won': False,
                    'game_over': False
                }
            else:
                return {
                    'response': TextSendMessage(text="استخدمت التلميح"),
                    'points': 0,
                    'correct': False,
                    'won': False,
                    'game_over': False
                }
        
        if answer_lower in ['جاوب', 'الجواب', 'answer']:
            words_list = "، ".join(self.current_challenge['words'])
            response_text = f"▪️ الإجابات المحتملة:\n\n{words_list}"
            
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
        
        # التحقق من الإجابة
        normalized_answer = normalize_text(answer)
        
        for word in self.current_challenge['words']:
            if normalized_answer == normalize_text(word):
                if normalized_answer in self.found_words:
                    return {
                        'response': TextSendMessage(text="هذه الكلمة وجدتها بالفعل"),
                        'points': 0,
                        'correct': False,
                        'won': False,
                        'game_over': False
                    }
                
                self.found_words.add(normalized_answer)
                points = 15 - (self.hints_used * 3)
                
                if user_id not in self.player_scores:
                    self.player_scores[user_id] = {'name': display_name, 'score': 0}
                self.player_scores[user_id]['score'] += points
                
                if self.question_number < self.total_questions:
                    response_text = f"▪️ صحيح {display_name}\n\n{answer}\n\n▫️ النقاط: {points}"
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
                'response': TextSendMessage(text="انتهت اللعبة"),
                'points': 0,
                'correct': False,
                'won': False,
                'game_over': True
            }
