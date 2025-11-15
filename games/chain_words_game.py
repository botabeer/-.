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

class ChainWordsGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.start_words = ["قلم", "كتاب", "مدرسة", "باب", "نافذة", "طاولة", "كرسي", "حديقة", "شجرة", "زهرة"]
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
        return TextSendMessage(
            text=f"▪️ لعبة سلسلة الكلمات\n\nالكلمة: {self.current_word}\n\nاكتب كلمة تبدأ بآخر حرف: {self.current_word[-1]}\n\n▫️ عدد الجولات: {self.max_rounds}"
        )
    
    def next_question(self):
        if self.round_count < self.max_rounds:
            last_letter = self.current_word[-1]
            return TextSendMessage(
                text=f"▪️ جولة {self.round_count + 1} من {self.max_rounds}\n\nالكلمة السابقة: {self.current_word}\n\nاكتب كلمة تبدأ بـ: {last_letter}"
            )
        return None
    
    def check_answer(self, answer, user_id, display_name):
        if not self.current_word:
            return None
        
        answer = answer.strip()
        last_letter = self.current_word[-1]
        
        # تطبيع التاء المربوطة والهاء
        normalized_last = last_letter
        if last_letter in ['ة', 'ه']:
            normalized_last = 'ه'
        
        normalized_answer = normalize_text(answer)
        
        # التحقق من أن الكلمة لم تستخدم
        if normalized_answer in self.used_words:
            return {
                'response': TextSendMessage(text="هذه الكلمة استخدمت من قبل"),
                'points': 0,
                'correct': False,
                'won': False,
                'game_over': False
            }
        
        # التحقق من الحرف الأول
        first_letter = answer[0].lower()
        if first_letter in ['ة', 'ه']:
            first_letter = 'ه'
        
        if first_letter == normalized_last or (normalized_last == 'ه' and first_letter in ['ه', 'ة']):
            self.used_words.add(normalized_answer)
            old_word = self.current_word
            self.current_word = answer
            self.round_count += 1
            
            points = 10
            
            if user_id not in self.player_scores:
                self.player_scores[user_id] = {'name': display_name, 'score': 0}
            self.player_scores[user_id]['score'] += points
            
            if self.round_count < self.max_rounds:
                response_text = f"▪️ صحيح {display_name}\n\n{old_word} ← {answer}\n\n▫️ النقاط: {points}"
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
        else:
            return {
                'response': TextSendMessage(text=f"يجب أن تبدأ الكلمة بحرف: {last_letter}"),
                'points': 0,
                'correct': False,
                'won': False,
                'game_over': False
            }
    
    def _end_game(self):
        if self.player_scores:
            sorted_players = sorted(self.player_scores.items(), key=lambda x: x[1]['score'], reverse=True)
            winner = sorted_players[0][1]
            all_scores = [(data['name'], data['score']) for uid, data in sorted_players]
            
            try:
                import sys
                import os
                sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
                from app import get_winner_card
                winner_card = get_winner_card(winner['name'], winner['score'], all_scores)
                
                return {
                    'points': 0,
                    'correct': False,
                    'won': True,
                    'game_over': True,
                    'winner_card': winner_card
                }
            except:
                return {
                    'response': TextSendMessage(text=f"▪️ انتهت اللعبة\n\nالفائز: {winner['name']}\nالنقاط: {winner['score']}"),
                    'points': 0,
                    'correct': False,
                    'won': False,
                    'game_over': True
                }
        else:
            return {
                'response': TextSendMessage(text="انتهت اللعبة"),
                'points': 0,
                'correct': False,
                'won': False,
                'game_over': True
            }
