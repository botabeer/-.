# ==============================================
# chain_words_game.py
# ==============================================
from linebot.models import TextSendMessage, FlexSendMessage
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
        
        self.C = {
            'bg': '#0a0e1a',
            'card': '#111827',
            'card2': '#1f2937',
            'text': '#F1F5F9',
            'text2': '#94A3B8',
            'sep': '#374151',
            'cyan': '#00D9FF',
            'cyan_glow': '#00E5FF',
        }
        
        self.start_words = ["قلم", "كتاب", "مدرسة", "باب", "نافذة", "طاولة", "كرسي", "حديقة", "شجرة", "زهرة"]
        self.current_word = None
        self.used_words = set()
        self.round_count = 0
        self.max_rounds = 5
        self.player_scores = {}
    
    def create_3d_box(self, contents, bg_color=None, padding="20px", margin="none"):
        return {
            "type": "box",
            "layout": "vertical",
            "contents": contents,
            "backgroundColor": bg_color or self.C['card2'],
            "cornerRadius": "16px",
            "paddingAll": padding,
            "margin": margin,
            "borderWidth": "1px",
            "borderColor": self.C['sep']
        }
    
    def get_game_card(self, word, last_letter, round_num):
        card = {
            "type": "bubble",
            "size": "mega",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "box", "layout": "vertical", "contents": [],
                             "width": "4px", "backgroundColor": self.C['cyan'],
                             "cornerRadius": "2px"},
                            {"type": "box", "layout": "vertical", "contents": [
                                {"type": "text", "text": "🔗 سلسلة الكلمات", "size": "xxl",
                                 "weight": "bold", "color": self.C['cyan']},
                                {"type": "text", "text": f"الجولة {round_num}/{self.max_rounds}",
                                 "size": "sm", "color": self.C['text2'], "margin": "sm"}
                            ], "margin": "md"}
                        ]
                    },
                    {"type": "separator", "margin": "xl", "color": self.C['sep']},
                    
                    self.create_3d_box([
                        {"type": "text", "text": "الكلمة السابقة", "size": "sm",
                         "color": self.C['text2'], "align": "center"},
                        {"type": "text", "text": word, "size": "xl",
                         "weight": "bold", "color": self.C['text'],
                         "align": "center", "margin": "sm"}
                    ], self.C['card'], "20px", "xl"),
                    
                    self.create_3d_box([
                        {"type": "text", "text": "ابدأ بحرف", "size": "sm",
                         "color": self.C['text2'], "align": "center"},
                        {"type": "text", "text": last_letter, "size": "xxl",
                         "weight": "bold", "color": self.C['cyan_glow'],
                         "align": "center", "margin": "md"}
                    ], self.C['card2'], "24px", "md"),
                    
                    {
                        "type": "box",
                        "layout": "horizontal",
                        "contents": [
                            {"type": "box", "layout": "vertical", "contents": [],
                             "backgroundColor": self.C['cyan'], "height": "6px",
                             "flex": round_num, "cornerRadius": "3px"},
                            {"type": "box", "layout": "vertical", "contents": [],
                             "backgroundColor": self.C['card2'], "height": "6px",
                             "flex": self.max_rounds - round_num, "cornerRadius": "3px"},
                        ],
                        "margin": "xl",
                        "spacing": "xs"
                    }
                ],
                "backgroundColor": self.C['bg'],
                "paddingAll": "24px"
            }
        }
        return card
    
    def start_game(self):
        self.current_word = random.choice(self.start_words)
        self.used_words = {normalize_text(self.current_word)}
        self.round_count = 1
        self.player_scores = {}
        
        last_letter = self.current_word[-1]
        card = self.get_game_card(self.current_word, last_letter, self.round_count)
        
        return FlexSendMessage(alt_text="سلسلة الكلمات", contents=card)
    
    def next_question(self):
        if self.round_count < self.max_rounds:
            last_letter = self.current_word[-1]
            card = self.get_game_card(self.current_word, last_letter, self.round_count + 1)
            return FlexSendMessage(alt_text=f"الجولة {self.round_count + 1}", contents=card)
        return None
    
    def check_answer(self, answer, user_id, display_name):
        if not self.current_word:
            return None
        
        answer = answer.strip()
        last_letter = self.current_word[-1]
        normalized_last = 'ه' if last_letter in ['ة', 'ه'] else last_letter
        normalized_answer = normalize_text(answer)
        
        if normalized_answer in self.used_words:
            return {'response': TextSendMessage(text="⚠️ هذه الكلمة استخدمت من قبل"), 'points': 0, 'correct': False}
        
        first_letter = 'ه' if answer[0].lower() in ['ة', 'ه'] else answer[0].lower()
        
        if first_letter == normalized_last:
            self.used_words.add(normalized_answer)
            old_word = self.current_word
            self.current_word = answer
            self.round_count += 1
            
            points = 2
            if user_id not in self.player_scores:
                self.player_scores[user_id] = {'name': display_name, 'score': 0}
            self.player_scores[user_id]['score'] += points
            
            # بطاقة النجاح
            success_card = {
                "type": "bubble",
                "size": "mega",
                "body": {
                    "type": "box",
                    "layout": "vertical",
                    "contents": [
                        self.create_3d_box([
                            {"type": "text", "text": "✨", "size": "xxl", "align": "center"},
                            {"type": "text", "text": "صحيح!", "size": "xxl",
                             "weight": "bold", "color": self.C['cyan'],
                             "align": "center", "margin": "md"}
                        ], self.C['card2']),
                        {"type": "separator", "margin": "xl", "color": self.C['sep']},
                        self.create_3d_box([
                            {"type": "text", "text": display_name, "size": "xl",
                             "weight": "bold", "color": self.C['text'], "align": "center"},
                            {"type": "text", "text": f"{old_word} ← {answer}",
                             "size": "md", "color": self.C['text2'], "align": "center", "margin": "sm"},
                            {"type": "text", "text": f"+{points} نقطة", "size": "lg",
                             "color": self.C['cyan_glow'], "align": "center", "margin": "sm"}
                        ], self.C['card'], "24px", "xl")
                    ],
                    "backgroundColor": self.C['bg'],
                    "paddingAll": "24px"
                }
            }
            
            if self.round_count < self.max_rounds:
                return {'response': FlexSendMessage(alt_text="صحيح", contents=success_card),
                        'points': points, 'correct': True, 'next_question': True}
            else:
                return self._end_game()
        else:
            return {'response': TextSendMessage(text=f"⚠️ يجب أن تبدأ الكلمة بحرف: {last_letter}"),
                    'points': 0, 'correct': False}
    
    def _end_game(self):
        if self.player_scores:
            sorted_players = sorted(self.player_scores.items(), key=lambda x: x[1]['score'], reverse=True)
            winner = sorted_players[0][1]
            all_scores = [(data['name'], data['score']) for uid, data in sorted_players]
            
            from app import get_winner_card
            winner_card = get_winner_card(winner['name'], winner['score'], all_scores)
            
            return {'points': 0, 'correct': False, 'won': True, 'game_over': True, 'winner_card': winner_card}
        else:
            return {'response': TextSendMessage(text="انتهت اللعبة"), 'points': 0, 'correct': False, 'game_over': True}
