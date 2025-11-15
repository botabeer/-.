from linebot.models import TextSendMessage, FlexSendMessage
import random
import re

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
            {"word": "نهار", "opposite": "ليل"},
            {"word": "أبيض", "opposite": "أسود"},
            {"word": "حلو", "opposite": "مر"},
            {"word": "جديد", "opposite": "قديم"}
        ]
        self.questions = []
        self.current_word = None
        self.hints_used = 0
        self.question_number = 0
        self.total_questions = 5
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
        self.questions = random.sample(self.all_words, min(self.total_questions, len(self.all_words)))
        self.question_number = 0
        self.player_scores = {}
        return self._next_question()
    
    def _next_question(self):
        self.question_number += 1
        self.current_word = self.questions[self.question_number - 1]
        self.hints_used = 0
        
        card = {
            "type": "bubble",
            "body": {
                "type": "box",
                "layout": "vertical",
                "contents": [
                    {
                        "type": "text",
                        "text": "لعبة الأضداد",
                        "size": "xl",
                        "weight": "bold",
                        "color": "#1C1C1E",
                        "align": "center"
                    },
                    {
                        "type": "text",
                        "text": f"سؤال {self.question_number} من {self.total_questions}",
                        "size": "sm",
                        "color": "#8E8E93",
                        "align": "center",
                        "margin": "sm"
                    },
                    {
                        "type": "separator",
                        "margin": "xl",
                        "color": "#F2F2F7"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "ما عكس:",
                                "size": "sm",
                                "color": "#8E8E93",
                                "align": "center"
                            },
                            {
                                "type": "text",
                                "text": self.current_word['word'],
                                "size": "xxl",
                                "weight": "bold",
                                "color": "#1C1C1E",
                                "align": "center",
                                "margin": "md"
                            }
                        ],
                        "backgroundColor": "#F2F2F7",
                        "cornerRadius": "12px",
                        "paddingAll": "20px",
                        "margin": "xl"
                    }
                ],
                "backgroundColor": "#FFFFFF",
                "paddingAll": "24px"
            },
            "footer": {
                "type": "box",
                "layout": "horizontal",
                "contents": [
                    {
                        "type": "button",
                        "action": {"type": "message", "label": "تلميح", "text": "لمح"},
                        "style": "secondary",
                        "height": "sm"
                    },
                    {
                        "type": "button",
                        "action": {"type": "message", "label": "الحل", "text": "جاوب"},
                        "style": "secondary",
                        "height": "sm"
                    }
                ],
                "spacing": "sm",
                "backgroundColor": "#F2F2F7",
                "paddingAll": "12px"
            }
        }
        
        return FlexSendMessage(alt_text="لعبة الأضداد", contents=card)
    
    def next_question(self):
        if self.question_number < self.total_questions:
            return self._next_question()
        return None
    
    def check_answer(self, answer, user_id, display_name):
        if not self.current_word:
            return None
        
        answer_lower = answer.strip().lower()
        
        # معالجة طلب التلميح
        if answer_lower in ['لمح', 'تلميح']:
            if self.hints_used == 0:
                opposite = self.current_word['opposite']
                hint = f"▫️ يبدأ بحرف: {opposite[0]}\n▫️ عدد الحروف: {len(opposite)}"
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
                    'response': TextSendMessage(text="▫️ استخدمت التلميح بالفعل"), 
                    'points': 0, 
                    'correct': False, 
                    'won': False, 
                    'game_over': False
                }
        
        # معالجة طلب عرض الحل
        if answer_lower in ['جاوب', 'الجواب', 'الحل']:
            response_text = f"▪️ الإجابة الصحيحة:\n\n{self.current_word['word']} ↔️ {self.current_word['opposite']}"
            return {
                'response': TextSendMessage(text=response_text), 
                'points': 0, 
                'correct': False, 
                'won': False, 
                'game_over': False, 
                'next_question': True
            }
        
        # التحقق من الإجابة الصحيحة
        if self.normalize_text(answer) == self.normalize_text(self.current_word['opposite']):
            # نظام النقاط الجديد: إجابة صحيحة +2، استخدام تلميح -1
            points = 2 - (self.hints_used * 1)
            
            if user_id not in self.player_scores:
                self.player_scores[user_id] = {'name': display_name, 'score': 0}
            self.player_scores[user_id]['score'] += points
            
            if self.question_number < self.total_questions:
                return {
                    'response': TextSendMessage(
                        text=f"✓ صحيح {display_name}\n\n{self.current_word['word']} ↔️ {self.current_word['opposite']}\n\n+{points} نقطة"
                    ),
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
            
            # بطاقة الفائز
            score_items = []
            for i, (uid, data) in enumerate(sorted_players, 1):
                bg_color = "#1C1C1E" if i == 1 else ("#8E8E93" if i == 2 else "#F2F2F7")
                text_color = "#FFFFFF" if i <= 2 else "#1C1C1E"
                
                score_items.append({
                    "type": "box",
                    "layout": "horizontal",
                    "contents": [
                        {"type": "text", "text": f"{i}.", "size": "sm", "color": text_color, "flex": 0},
                        {"type": "text", "text": data['name'], "size": "sm", "color": text_color, "flex": 3, "margin": "md", "wrap": True},
                        {"type": "text", "text": str(data['score']), "size": "sm", "color": text_color, "flex": 1, "align": "end", "weight": "bold"}
                    ],
                    "backgroundColor": bg_color,
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
                            "type": "text",
                            "text": "🏆 انتهت اللعبة",
                            "size": "xl",
                            "weight": "bold",
                            "color": "#1C1C1E",
                            "align": "center"
                        },
                        {
                            "type": "separator",
                            "margin": "xl",
                            "color": "#F2F2F7"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "text",
                                    "text": "الفائز",
                                    "size": "sm",
                                    "color": "#8E8E93",
                                    "align": "center"
                                },
                                {
                                    "type": "text",
                                    "text": winner['name'],
                                    "size": "xl",
                                    "weight": "bold",
                                    "color": "#1C1C1E",
                                    "align": "center",
                                    "margin": "sm",
                                    "wrap": True
                                },
                                {
                                    "type": "text",
                                    "text": f"{winner['score']} نقطة",
                                    "size": "md",
                                    "color": "#8E8E93",
                                    "align": "center",
                                    "margin": "sm"
                                }
                            ],
                            "margin": "xl"
                        },
                        {
                            "type": "separator",
                            "margin": "xl",
                            "color": "#F2F2F7"
                        },
                        {
                            "type": "text",
                            "text": "النتائج النهائية",
                            "size": "md",
                            "weight": "bold",
                            "color": "#1C1C1E",
                            "margin": "xl"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": score_items,
                            "margin": "md"
                        }
                    ],
                    "backgroundColor": "#FFFFFF",
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
        else:
            return {
                'response': TextSendMessage(text="▪️ انتهت اللعبة"), 
                'points': 0, 
                'correct': False, 
                'won': False, 
                'game_over': True
            }
