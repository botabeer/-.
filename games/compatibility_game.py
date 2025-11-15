from linebot.models import TextSendMessage, FlexSendMessage
import random

class CompatibilityGame:
    def __init__(self, line_bot_api):
        self.line_bot_api = line_bot_api
        self.waiting_for_names = True
        
        # الألوان - iOS Style
        self.colors = {
            'primary': '#1C1C1E',
            'text': '#1C1C1E',
            'text_light': '#8E8E93',
            'surface': '#F2F2F7',
            'white': '#FFFFFF'
        }
    
    def start_game(self):
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
                                "text": "لعبة التوافق",
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
                                "text": "للتسلية فقط",
                                "size": "sm",
                                "color": self.colors['text_light'],
                                "align": "center"
                            }
                        ],
                        "margin": "md"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "اكتب اسمين مفصولين بمسافة",
                                "size": "md",
                                "color": self.colors['text'],
                                "align": "center",
                                "wrap": True,
                                "weight": "bold"
                            },
                            {
                                "type": "text",
                                "text": "نص فقط بدون رموز",
                                "size": "sm",
                                "color": self.colors['text_light'],
                                "align": "center",
                                "margin": "md"
                            },
                            {
                                "type": "box",
                                "layout": "vertical",
                                "contents": [
                                    {
                                        "type": "text",
                                        "text": "مثال: اسم اسم",
                                        "size": "sm",
                                        "color": self.colors['text'],
                                        "align": "center"
                                    }
                                ],
                                "backgroundColor": self.colors['white'],
                                "cornerRadius": "8px",
                                "paddingAll": "12px",
                                "margin": "md"
                            },
                            {
                                "type": "text",
                                "text": "لا تُحسب نقاط لهذه اللعبة",
                                "size": "xs",
                                "color": self.colors['text_light'],
                                "align": "center",
                                "margin": "lg"
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
        
        return FlexSendMessage(alt_text="لعبة التوافق", contents=card)
    
    def check_answer(self, answer, user_id, display_name):
        if not self.waiting_for_names:
            return None
        
        parts = answer.strip().split()
        
        if len(parts) < 2:
            return {
                'response': TextSendMessage(
                    text="يجب كتابة اسمين مفصولين بمسافة\n\nمثال: اسم اسم"
                ),
                'points': 0,
                'correct': False,
                'won': False,
                'game_over': False
            }
        
        name1 = parts[0]
        name2 = parts[1]
        
        # نسبة توافق عشوائية
        compatibility = random.randint(50, 100)
        
        # رسائل حسب النسبة
        if compatibility >= 90:
            message = "توافق مثالي"
            emoji = ""
        elif compatibility >= 75:
            message = "توافق ممتاز"
            emoji = ""
        elif compatibility >= 60:
            message = "توافق جيد"
            emoji = ""
        else:
            message = "توافق متوسط"
            emoji = ""
        
        self.waiting_for_names = False
        
        # بطاقة النتيجة
        result_card = {
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
                                "text": "نسبة التوافق",
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
                                "text": f"{name1} 🖤 {name2}",
                                "size": "lg",
                                "weight": "bold",
                                "color": self.colors['text'],
                                "align": "center",
                                "wrap": True
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
                                "text": f"{compatibility}%",
                                "size": "xxl",
                                "weight": "bold",
                                "color": self.colors['text'],
                                "align": "center"
                            },
                            {
                                "type": "text",
                                "text": f"{emoji} {message}",
                                "size": "md",
                                "color": self.colors['text_light'],
                                "align": "center",
                                "margin": "sm"
                            }
                        ],
                        "backgroundColor": self.colors['surface'],
                        "cornerRadius": "12px",
                        "paddingAll": "20px",
                        "margin": "lg"
                    },
                    {
                        "type": "box",
                        "layout": "vertical",
                        "contents": [
                            {
                                "type": "text",
                                "text": "للتسلية فقط - لا تُحسب نقاط",
                                "size": "xs",
                                "color": self.colors['text_light'],
                                "align": "center"
                            }
                        ],
                        "margin": "lg"
                    }
                ],
                "backgroundColor": self.colors['white'],
                "paddingAll": "24px"
            }
        }
        
        return {
            'response': FlexSendMessage(alt_text="نسبة التوافق", contents=result_card),
            'points': 0,  # لا نقاط لهذه اللعبة
            'correct': True,
            'won': False,
            'game_over': True
        }
