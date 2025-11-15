from linebot.models import TextSendMessage, FlexSendMessage
import random
import re
from datetime import datetime

class FastTypingGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.current_word = None
        self.first_correct = None
        self.start_time = None
        self.time_limit = 30
        self.scores = {}
        
        # الألوان - iOS Style
        self.colors = {
            'primary': '#1C1C1E',
            'text': '#1C1C1E',
            'text_light': '#8E8E93',
            'surface': '#F2F2F7',
            'white': '#FFFFFF'
        }
        
        self.words = [
            "سرعة", "كتابة", "برمجة", "حاسوب", "إنترنت", "تطبيق", "موقع", "شبكة",
            "تقنية", "ذكاء", "تطوير", "مبرمج", "لغة", "كود", "برنامج", "نظام",
            "بيانات", "خادم", "واجهة", "تصميم", "مشروع", "فريق", "عمل", "هدف"
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
                                "text": "الكتابة السريعة",
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
                                "text": "اكتب هذه الكلمة بأسرع وقت",
                                "size": "sm",
                                "color": self.colors['text_light'],
                                "align": "center",
                                "wrap": True
                            },
                            {
                                "type": "text",
                                "text": self.current_word,
                                "size": "xxl",
                                "weight": "bold",
                                "color": self.colors['text'],
                                "align": "center",
                                "margin": "lg"
                            },
                            {
                                "type": "box",
                                "layout": "horizontal",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "⏱",
                                        "size": "sm",
                                        "color": self.colors['text_light'],
                                        "flex": 0
                                    },
                                    {
                                        "type": "text",
                                        "text": f"الوقت: {self.time_limit} ثانية",
                                        "size": "sm",
                                        "color": self.colors['text_light'],
                                        "margin": "sm"
                                    }
                                ],
                                "margin": "lg",
                                "justifyContent": "center"
                            },
                            {
                                "type": "text",
                                "text": "أول إجابة صحيحة تفوز",
                                "size": "xs",
                                "color": self.colors['text_light'],
                                "align": "center",
                                "margin": "md"
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
        
        return FlexSendMessage(alt_text="الكتابة السريعة", contents=card)
    
    def check_answer(self, text, user_id, display_name):
        # التحقق من الوقت
        if self.start_time:
            elapsed = (datetime.now() - self.start_time).seconds
            if elapsed > self.time_limit:
                if not self.first_correct:
                    return {
                        'correct': False,
                        'game_over': True,
                        'response': TextSendMessage(text=f"انتهى الوقت\n\nلم يجب أحد\n\nالكلمة: {self.current_word}")
                    }
                return None
        
        # إذا كان هناك فائز بالفعل
        if self.first_correct:
            return None
        
        # التحقق من الإجابة
        text_normalized = self.normalize_text(text)
        word_normalized = self.normalize_text(self.current_word)
        
        if text_normalized == word_normalized:
            elapsed_time = (datetime.now() - self.start_time).total_seconds()
            
            # حساب النقاط حسب السرعة
            if elapsed_time <= 5:
                points = 20
            elif elapsed_time <= 10:
                points = 15
            elif elapsed_time <= 15:
                points = 10
            elif elapsed_time <= 20:
                points = 5
            else:
                points = 2
            
            self.first_correct = user_id
            if user_id not in self.scores:
                self.scores[user_id] = {'name': display_name, 'score': 0}
            self.scores[user_id]['score'] += points
            
            # بطاقة الفوز
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
                                    "text": "🏆",
                                    "size": "xxl",
                                    "align": "center"
                                }
                            ]
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
                                    "text": display_name,
                                    "size": "xl",
                                    "weight": "bold",
                                    "color": self.colors['text'],
                                    "align": "center",
                                    "margin": "sm",
                                    "wrap": True
                                }
                            ],
                            "margin": "lg"
                        },
                        {
                            "type": "box",
                            "layout": "vertical",
                            "contents": [
                                {
                                    "type": "box",
                                    "layout": "horizontal",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": "⏱ الوقت",
                                            "size": "sm",
                                            "color": self.colors['text_light'],
                                            "flex": 1
                                        },
                                        {
                                            "type": "text",
                                            "text": f"{elapsed_time:.2f}s",
                                            "size": "md",
                                            "weight": "bold",
                                            "color": self.colors['text'],
                                            "flex": 1,
                                            "align": "end"
                                        }
                                    ]
                                },
                                {
                                    "type": "box",
                                    "layout": "horizontal",
                                    "contents": [
                                        {
                                            "type": "text",
                                            "text": "النقاط",
                                            "size": "sm",
                                            "color": self.colors['text_light'],
                                            "flex": 1
                                        },
                                        {
                                            "type": "text",
                                            "text": f"+{points}",
                                            "size": "md",
                                            "weight": "bold",
                                            "color": self.colors['text'],
                                            "flex": 1,
                                            "align": "end"
                                        }
                                    ],
                                    "margin": "md"
                                }
                            ],
                            "backgroundColor": self.colors['surface'],
                            "cornerRadius": "12px",
                            "paddingAll": "16px",
                            "margin": "lg"
                        }
                    ],
                    "backgroundColor": self.colors['white'],
                    "paddingAll": "24px"
                }
            }
            
            return {
                'correct': True,
                'points': points,
                'won': True,
                'game_over': True,
                'response': FlexSendMessage(alt_text="الفائز", contents=winner_card),
                'winner_card': winner_card
            }
        
        return None
