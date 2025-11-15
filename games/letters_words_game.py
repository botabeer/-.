from linebot.models import TextSendMessage, FlexSendMessage
import random
import re

class ChainWordsGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.start_words = ["قلم", "كتاب", "مدرسة", "باب", "نافذة", "طاولة", "سماء", "ورد", "جمل", "ليل"]
        self.current_word = None
        self.used_words = set()
        self.round_count = 0
        self.max_rounds = 5
        self.player_scores = {}
        
        # الألوان - iOS Style
        self.colors = {
            'primary': '#1C1C1E',
            'text': '#1C1C1E',
            'text_light': '#8E8E93',
            'surface': '#F2F2F7',
            'white': '#FFFFFF'
        }
    
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
        return self._create_question_card()
    
    def _create_question_card(self):
        """بطاقة السؤال"""
        last_letter = self.current_word[-1]
        
        card = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "سلسلة الكلمات",
                                "size": "xl",
                                "weight": "bold",
                                "color": self.colors['white'],
                                "align": "center"
                            }
                        ],
                        "backgroundColor": self.colors['primary'],
                        "cornerRadius": "16px",
                        "paddingAll": "20px"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": f"جولة {self.round_count + 1} من {self.max_rounds}",
                                "size": "sm",
                                "color": self.colors['text_light'],
                                "align": "center"
                            }
                        ],
                        "margin": "lg"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "الكلمة السابقة",
                                "size": "xs",
                                "color": self.colors['text_light'],
                                "align": "center"
                            },
                            {
                                "type": "text",
                                "text": self.current_word,
                                "size": "xxl",
                                "weight": "bold",
                                "color": self.colors['text'],
                                "align": "center",
                                "margin": "sm"
                            },
                            {
                                "type": "text",
                                "text": f"اكتب كلمة تبدأ بحرف: {last_letter}",
                                "size": "sm",
                                "color": self.colors['text'],
                                "align": "center",
                                "margin": "md",
                                "wrap": True
                            }
                        ],
                        "backgroundColor": self.colors['surface'],
                        "cornerRadius": "12px",
                        "paddingAll": "20px",
                        "margin": "lg"
                    }
                ],
                "backgroundColor": self.colors['white'],
                "paddingAll": "24px"
            }
        }
        
        return FlexSendMessage(alt_text="سلسلة الكلمات", contents=card)
    
    def next_question(self):
        if self.round_count < self.max_rounds:
            return self._create_question_card()
        return None
    
    def check_answer(self, answer, user_id, display_name):
        if not self.current_word:
            return None
        
        answer = answer.strip()
        last_letter = self.current_word[-1]
        normalized_last = 'ه' if last_letter in ['ة', 'ه'] else last_letter
        normalized_answer = self.normalize_text(answer)
        
        # التحقق من الكلمة المستخدمة
        if normalized_answer in self.used_words:
            return {
                'response': TextSendMessage(text="هذه الكلمة استخدمت من قبل"),
                'points': 0,
                'correct': False,
                'won': False,
                'game_over': False
            }
        
        # التحقق من الحرف الأول
        first_letter = 'ه' if answer[0].lower() in ['ة', 'ه'] else answer[0].lower()
        
        if first_letter == normalized_last:
            self.used_words.add(normalized_answer)
            old_word = self.current_word
            self.current_word = answer
            self.round_count += 1
            
            points = 2  # نظام النقاط الجديد
            if user_id not in self.player_scores:
                self.player_scores[user_id] = {'name': display_name, 'score': 0}
            self.player_scores[user_id]['score'] += points
            
            if self.round_count < self.max_rounds:
                return {
                    'response': TextSendMessage(text=f"إجابة صحيحة {display_name}\n\n{old_word} ← {answer}\n\n+{points} نقطة"),
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
        """بطاقة نهاية اللعبة"""
        if not self.player_scores:
            return {
                'response': TextSendMessage(text="انتهت اللعبة"),
                'points': 0,
                'correct': False,
                'won': False,
                'game_over': True
            }
        
        sorted_players = sorted(self.player_scores.items(), key=lambda x: x[1]['score'], reverse=True)
        winner = sorted_players[0][1]
        
        # بناء قائمة اللاعبين
        score_items = []
        for i, (uid, data) in enumerate(sorted_players, 1):
            if i == 1:
                emoji = "🥇"
                bg = self.colors['primary']
                tc = self.colors['white']
            elif i == 2:
                emoji = "🥈"
                bg = self.colors['text_light']
                tc = self.colors['white']
            elif i == 3:
                emoji = "🥉"
                bg = self.colors['text_light']
                tc = self.colors['white']
            else:
                emoji = f"{i}"
                bg = self.colors['surface']
                tc = self.colors['text']
            
            score_items.append({
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {"type": "text", "text": emoji, "size": "sm", "color": tc, "flex": 0, "weight": "bold"},
                    {"type": "text", "text": data['name'], "size": "sm", "color": tc, "flex": 3, "margin": "md", "wrap": True},
                    {"type": "text", "text": f"{data['score']}", "size": "sm", "color": tc, "flex": 1, "align": "end", "weight": "bold"}
                ],
                "backgroundColor": bg,
                "cornerRadius": "12px",
                "paddingAll": "12px",
                "margin": "sm" if i > 1 else "none"
            })
        
        winner_card = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "انتهت اللعبة",
                                "size": "xl",
                                "weight": "bold",
                                "color": self.colors['white'],
                                "align": "center"
                            }
                        ],
                        "backgroundColor": self.colors['primary'],
                        "cornerRadius": "16px",
                        "paddingAll": "20px"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "الفائز",
                                "size": "sm",
                                "color": self.colors['text_light'],
                                "align": "center"
                            },
                            {
                                "type": "text",
                                "text": winner['name'],
                                "size": "xl",
                                "weight": "bold",
                                "color": self.colors['text'],
                                "align": "center",
                                "margin": "sm",
                                "wrap": True
                            },
                            {
                                "type": "text",
                                "text": f"{winner['score']} نقطة",
                                "size": "md",
                                "color": self.colors['text_light'],
                                "align": "center",
                                "margin": "sm"
                            }
                        ],
                        "margin": "xl"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "النتائج النهائية",
                                "size": "md",
                                "weight": "bold",
                                "color": self.colors['text'],
                                "margin": "xl"
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": score_items,
                                "margin": "md"
                            }
                        ]
                    }
                ],
                "backgroundColor": self.colors['white'],
                "paddingAll": "24px"
            }
        }
        
        return {
            'response': FlexSendMessage(alt_text="الفائز", contents=winner_card),
            'points': 0,
            'correct': False,
            'won': False,
            'game_over': True,
            'winner_card': winner_card
        }
